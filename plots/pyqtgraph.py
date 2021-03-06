"""
Live plotting using pyqtgraph
"""
import numpy as np
import pyqtgraph as pg
import pyqtgraph.multiprocess as pgmp
import warnings
from collections import namedtuple

from .base import BasePlot
from .colors import color_cycle, colorscales


TransformState = namedtuple('TransformState', 'translate scale revisit')


class QtPlot(BasePlot):
    """
    Plot x/y lines or x/y/z heatmap data. The first trace may be included
    in the constructor, other traces can be added with QtPlot.add().

    For information on how x/y/z *args are handled see add() in the base
    plotting class.

    Args:
        *args: shortcut to provide the x/y/z data. See BasePlot.add

        figsize: (width, height) tuple in pixels to pass to GraphicsWindow
            default (1000, 600)
        interval: period in seconds between update checks
            default 0.25
        theme: tuple of (foreground_color, background_color), where each is
            a valid Qt color. default (dark gray, white), opposite the pyqtgraph
            default of (white, black)

        **kwargs: passed along to QtPlot.add() to add the first data trace
    """
    proc = None
    rpg = None

    def __init__(self, *args, figsize=(1000, 600), interval=0.25,
                 windowTitle='', theme=((60, 60, 60), 'w'), show_window=True, remote=True, **kwargs):
        super().__init__(interval)

        self.theme = theme

        if remote:
            if not self.__class__.proc:
                self._init_qt()
        else:
            # overrule the remote pyqtgraph class
            self.rpg = pg
        self.win = self.rpg.GraphicsWindow(title=windowTitle)
        self.win.setBackground(theme[1])
        self.win.resize(*figsize)
        self.subplots = [self.add_subplot()]

        if args or kwargs:
            self.add(*args, **kwargs)

        if not show_window:
            self.win.hide()

    def _init_qt(self):
        # starting the process for the pyqtgraph plotting
        # You do not want a new process to be created every time you start a
        # run, so this only starts once and stores the process in the class
        pg.mkQApp()
        self.__class__.proc = pgmp.QtProcess()  # pyqtgraph multiprocessing
        self.__class__.rpg = self.proc._import('pyqtgraph')

    def clear(self):
        """
        Clears the plot window and removes all subplots and traces
        so that the window can be reused.
        """
        self.win.clear()
        self.traces = []
        self.subplots = []

    def add_subplot(self):
        subplot_object = self.win.addPlot()

        for side in ('left', 'bottom'):
            ax = subplot_object.getAxis(side)
            ax.setPen(self.theme[0])
            ax._qcodes_label = ''

        return subplot_object

    def add_to_plot(self, subplot=1, **kwargs):
        if subplot > len(self.subplots):
            for i in range(subplot - len(self.subplots)):
                self.subplots.append(self.add_subplot())
        subplot_object = self.subplots[subplot - 1]

        if 'z' in kwargs:
            plot_object = self._draw_image(subplot_object, **kwargs)
        else:
            plot_object = self._draw_plot(subplot_object, **kwargs)

        self._update_labels(subplot_object, kwargs)
        prev_default_title = self.get_default_title()

        self.traces.append({
            'config': kwargs,
            'plot_object': plot_object
        })

        if prev_default_title == self.win.windowTitle():
            self.win.setWindowTitle(self.get_default_title())

    def _draw_plot(self, subplot_object, y, x=None, color=None, width=None,
                   antialias=None, **kwargs):
        if 'pen' not in kwargs:
            if color is None:
                cycle = color_cycle
                color = cycle[len(self.traces) % len(cycle)]
            if width is None:
                width = 2
            kwargs['pen'] = self.rpg.mkPen(color, width=width)

        if antialias is None:
            # looks a lot better antialiased, but slows down with many points
            # TODO: dynamically update this based on total # of points
            antialias = (len(y) < 1000)

        # If a marker symbol is desired use the same color as the line
        if any([('symbol' in key) for key in kwargs]):
            if 'symbolPen' not in kwargs:
                symbol_pen_width = 0.5 if antialias else 1.0
                kwargs['symbolPen'] = self.rpg.mkPen('444',
                                                     width=symbol_pen_width)
            if 'symbolBrush' not in kwargs:
                kwargs['symbolBrush'] = color

        # suppress warnings when there are only NaN to plot
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', 'All-NaN axis encountered')
            warnings.filterwarnings('ignore', 'All-NaN slice encountered')
            pl = subplot_object.plot(*self._line_data(x, y),
                                     antialias=antialias, **kwargs)
        return pl

    def _line_data(self, x, y):
        return [self._clean_array(arg) for arg in [x, y] if arg is not None]

    def _draw_image(self, subplot_object, z, x=None, y=None, cmap='hot',
                    **kwargs):
        img = self.rpg.ImageItem()
        subplot_object.addItem(img)

        hist = self.rpg.HistogramLUTItem()
        hist.setImageItem(img)
        hist.axis.setPen(self.theme[0])
        if 'zlabel' in kwargs:  # used to specify a custom zlabel
            hist.axis.setLabel(kwargs['zlabel'])
        else:  # otherwise extracts the label from the dataarray
            hist.axis.setLabel(self.get_label(z))
        # TODO - ensure this goes next to the correct subplot?
        self.win.addItem(hist)

        plot_object = {
            'image': img,
            'hist': hist,
            'histlevels': hist.getLevels(),
            'cmap': cmap,
            'scales': {
                'x': TransformState(0, 1, True),
                'y': TransformState(0, 1, True)
            }
        }

        self._update_image(plot_object, {'x': x, 'y': y, 'z': z})
        self._update_cmap(plot_object)

        return plot_object

    def _update_image(self, plot_object, config):
        z = config['z']
        img = plot_object['image']
        hist = plot_object['hist']
        scales = plot_object['scales']

        # make sure z is a *new* numpy float array (pyqtgraph barfs on ints),
        # and replace nan with minimum val bcs I can't figure out how to make
        # pyqtgraph handle nans - though the source does hint at a way:
        # http://www.pyqtgraph.org/documentation/_modules/pyqtgraph/widgets/ColorMapWidget.html
        # see class RangeColorMapItem
        z = np.asfarray(z).T
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            try:
                z_range = (np.nanmin(z), np.nanmax(z))
            except:
                # we get a warning here when z is entirely NaN
                # nothing to plot, so give up.
                return
        z[np.where(np.isnan(z))] = z_range[0]

        hist_range = hist.getLevels()
        if hist_range == plot_object['histlevels']:
            plot_object['histlevels'] = z_range
            hist.setLevels(*z_range)
            hist_range = z_range

        img.setImage(self._clean_array(z), levels=hist_range)

        scales_changed = False
        for axletter, axscale in scales.items():
            if axscale.revisit:
                axdata = config.get(axletter, None)
                newscale = self._get_transform(axdata)
                if (newscale.translate != axscale.translate or
                        newscale.scale != axscale.scale):
                    scales_changed = True
                scales[axletter] = newscale

        if scales_changed:
            img.resetTransform()
            img.translate(scales['x'].translate, scales['y'].translate)
            img.scale(scales['x'].scale, scales['y'].scale)

    def _update_cmap(self, plot_object):
        gradient = plot_object['hist'].gradient
        gradient.setColorMap(self._cmap(plot_object['cmap']))

    def set_cmap(self, cmap, traces=None):
        if isinstance(traces, int):
            traces = (traces,)
        elif traces is None:
            traces = range(len(self.traces))

        for i in traces:
            plot_object = self.traces[i]['plot_object']
            if not isinstance(plot_object, dict) or 'hist' not in plot_object:
                continue

            plot_object['cmap'] = cmap
            self._update_cmap(plot_object)

    def _get_transform(self, array):
        """
        pyqtgraph seems to only support uniform pixels in image plots.

        for a given setpoint array, extract the linear transform it implies
        if the setpoint data is *not* linear (or close to it), or if it's not
        uniform in any nested dimensions, issue a warning and return the
        default transform of 0, 1

        returns namedtuple TransformState(translate, scale, revisit)

        in pyqtgraph:
        translate means how many pixels to shift the image, away
            from the bottom or left edge being at zero on the axis
        scale means the data delta

        revisit is True if we just don't have enough info to scale yet,
        but we might later.
        """

        if array is None:
            return TransformState(0, 1, True)

        # do we have enough confidence in the setpoint data we've seen
        # so far that we don't have to repeat this as more data comes in?
        revisit = False

        # somewhat arbitrary - if the first 20% of the data or at least
        # 10 rows is uniform, assume it's uniform thereafter
        MINROWS = 10
        MINFRAC = 0.2

        # maximum setpoint deviation from linear to accept is 10% of a pixel
        MAXPX = 0.1

        if hasattr(array[0], '__len__'):
            # 2D array: check that all (non-empty) elements are congruent
            inner_len = max(len(row) for row in array)
            collapsed = np.array([np.nan] * inner_len)
            rows_before_trusted = max(MINROWS, len(array) * MINFRAC)
            for i, row in enumerate(array):
                for j, val in enumerate(row):
                    if np.isnan(val):
                        if i < rows_before_trusted:
                            revisit = True
                        continue
                    if np.isnan(collapsed[j]):
                        collapsed[j] = val
                    elif val != collapsed[j]:
                        warnings.warn(
                            'nonuniform nested setpoint array passed to '
                            'pyqtgraph. ignoring, using default scaling.')
                        return TransformState(0, 1, False)
        else:
            collapsed = array

        if np.isnan(collapsed).any():
            revisit = True

        indices_setpoints = list(zip(*((i, s) for i, s in enumerate(collapsed)
                                     if not np.isnan(s))))
        if not indices_setpoints:
            return TransformState(0, 1, revisit)

        indices, setpoints = indices_setpoints
        npts = len(indices)
        if npts == 1:
            indices = indices + (indices[0] + 1,)
            setpoints = setpoints + (setpoints[0] + 1,)

        i0 = indices[0]
        s0 = setpoints[0]
        total_di = indices[-1] - i0
        total_ds = setpoints[-1] - s0

        if total_ds == 0:
            warnings.warn('zero setpoint range passed to pyqtgraph. '
                          'ignoring, using default scaling.')
            return TransformState(0, 1, False)

        for i, s in zip(indices[1:-1], setpoints[1:-1]):
            icalc = i0 + (s - s0) * total_di / total_ds
            if np.abs(i - icalc) > MAXPX:
                warnings.warn('nonlinear setpoint array passed to pyqtgraph. '
                              'ignoring, using default scaling.')
                return TransformState(0, 1, False)

        scale = total_ds / total_di
        # extra 0.5 translation to get the first setpoint at the center of
        # the first pixel
        translate = s0 - (i0 + 0.5) * scale

        return TransformState(translate, scale, revisit)

    def _update_labels(self, subplot_object, config):
        """
        Updates x and y labels, by default tries to extract label from
        the DataArray objects located in the trace config. Custom labels
        can be specified the **kwargs "xlabel" and "ylabel"
        """
        for axletter, side in (('x', 'bottom'), ('y', 'left')):
            ax = subplot_object.getAxis(side)
            # pyqtgraph doesn't seem able to get labels, only set
            # so we'll store it in the axis object and hope the user
            # doesn't set it separately before adding all traces
            if axletter+'label' in config and not ax._qcodes_label:
                label = config[axletter+'label']
                ax._qcodes_label = label
                ax.setLabel(label)
            if axletter in config and not ax._qcodes_label:
                label = self.get_label(config[axletter])
                if label:
                    ax._qcodes_label = label
                    ax.setLabel(label)

    def update_plot(self):
        for trace in self.traces:
            config = trace['config']
            plot_object = trace['plot_object']
            if 'z' in config:
                self._update_image(plot_object, config)
            else:
                plot_object.setData(*self._line_data(config['x'], config['y']))

    def _clean_array(self, array):
        """
        we can't send a DataArray to remote pyqtgraph for some reason,
        so send the plain numpy array
        """
        if hasattr(array, 'ndarray') and isinstance(array.ndarray, np.ndarray):
            return array.ndarray
        return array

    def _cmap(self, scale):
        if isinstance(scale, str):
            if scale in colorscales:
                values, colors = zip(*colorscales[scale])
            else:
                raise ValueError(scale + ' not found in colorscales')
        elif len(scale) == 2:
            values, colors = scale

        return self.rpg.ColorMap(values, colors)

    def _repr_png_(self):
        """
        Create a png representation of the current window.
        """
        image = self.win.grab()
        byte_array = self.rpg.QtCore.QByteArray()
        buffer = self.rpg.QtCore.QBuffer(byte_array)
        buffer.open(self.rpg.QtCore.QIODevice.ReadWrite)
        image.save(buffer, 'PNG')
        buffer.close()
        return bytes(byte_array._getValue())
    
    def save(self, filename=None):
        """
        Save current plot to filename, by default
        to the location corresponding to the default 
        title.

        Args:
            filename (Optional[str]): Location of the file
        """
        default = "{}.png".format(self.get_default_title())
        filename = filename or default
        image = self.win.grab()
        image.save(filename, "PNG", 0)
