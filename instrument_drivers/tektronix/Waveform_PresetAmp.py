# 18.04.2016
# TO DO: Check amplitude increment in waveform generation
# Bug(maybe): Cannot create sequence for specified channel - interpolate to returns sequence of element without any info about channels 


import numpy as np
import matplotlib.pyplot as plt



        
                        
            
class Pulse():
    '''
    TO DO...
            
    '''
    
    
    
    def __init__(self, waveform_name, AWG_clock, TimeUnits, AmpUnits): 
        
              
        self.AWG_clock = AWG_clock
        self.AWG_period = 1/float(self.AWG_clock)     # Calculating AWG period
        
        self.amplitudes = dict()
        self.timings = dict()
        self.marker1_dict = dict()
        self.marker2_dict = dict()
    
        self.waveform = np.array([])                                
        self.unscaled_waveform = np.array([])                                
        self.marker1 = np.array([])
        self.marker2 = np.array([])
        
        self.TimeUnitsDict = {'s':1,'ms':1e-3,'us':1e-6}
        self.AmpUnitsDict = {'V':1,'mV':1e-3,'uV':1e-6}
        
        if TimeUnits not in self.TimeUnitsDict.keys():
            raise Exception('Error: Not valdid time units! Valid units are: "s","ms","us"')
            
        if AmpUnits not in self.AmpUnitsDict.keys():
            raise Exception('Error: Not valdid amplitude units! Valid units are: "V","mV","uV"')
        
        self.TimeUnitsKey = TimeUnits  
        self.TimeUnits = self.TimeUnitsDict[self.TimeUnitsKey]
        self.AmpUnitsKey = AmpUnits
        self.AmpUnits = self.AmpUnitsDict[self.AmpUnitsKey]


        
        self.waveform_name = waveform_name
        #self.Max_amp = 0
    def setAWG_clock(self,AWG_clock=1e8):
        self.AWG_clock = AWG_clock;
        self.AWG_period = 1/float(self.AWG_clock) 
        self.ModifyWaveform() 
                
    def setAmplitudes(self, **kwargs):
        '''
        Sets a pulse amplitude section by section in mV. 
        
        Input:
            **kwargs (dictionary) : Dictionary of amplitude values. Values are in mV
                                    Keys are: T1,T2... , 
                                    Values are tuples: (val1,val2),(val,val4)...
                                    
                                    Example: p.setAmplitudes(T1 = (100,200),T3 = (150,200),T2 = (300,300))
        
        Output:
            None
            
        Note: Keys for self.amplitudes and self.timings must be the same (T1,T2,T3,T4...)
        ''' 
          
        for key, item in kwargs.iteritems():
            self.amplitudes[key] = item
        self.ModifyWaveform()       # Every time amplitudes are modified -> complete pulse is modified
            
            
            
    def setMarker1(self, **kwargs):
        '''TO DO'''
        for key, item in kwargs.iteritems():
            self.marker1_dict[key] = item
        self.ModifyWaveform()   # Every time marker1 is modified -> complete pulse is modified
            
            
    def setMarker2(self, **kwargs):
        '''TO DO'''
        for key, item in kwargs.iteritems():
            self.marker2_dict[key] = item      
        self.ModifyWaveform()    # Every time marker2 is modified -> complete pulse is modified  

            
            
    
    def setTimings(self, **kwargs):
        '''TO DO'''
        for key, item in kwargs.iteritems():
            if item < 0 or item == 0:   # Checking if timing segments of a pulse are all positive     # Added 09.03_13:20
                 raise Exception('All timing must be positive')                                      # Added 09.03_13:20
            self.timings[key] = item
        self.ModifyWaveform()     # Every time timings are modified -> complete pulse is modified 
            
            
    
    def ModifyWaveform(self):          
        '''
        Creates/Modifies waveform arrays: self.waveform, self.marker1 and self.marker2,   
            based on self.amplitudes, self.timings, self.marker1_dict, self.marker2_dict.
            Every time some of these values are changed this function makes new pulse if their lengths are the same.
        
        '''

        if not(len(self.amplitudes)==len(self.timings)==len(self.marker1_dict)==len(self.marker2_dict)):  # Do modification only if all of these are of the same length - SYNCHRONIZATION
            return 0
        
        self.waveform = np.array([]) # Erase previous waveform
        self.marker1 = np.array([])  # Erase previous marker 1
        self.marker2 = np.array([])  # Erase previous marker 2
        
        for key in sorted(self.amplitudes.iterkeys()):  # Sort amplitudes dict and iterate trough its element from the frist one
            
            
            Length = self.rescaleLength(self.timings[key]) # Rescaling length 
            
            Start_amp = self.amplitudes[key][0]         # Amplitude of starting wavefrom part             
            End_amp = self.amplitudes[key][1]           # Amplitude of ending wavefrom part   
            self.waveform = np.concatenate((self.waveform,np.linspace(Start_amp,End_amp,Length)))
            
            Marker1 = self.marker1_dict[key]    # Value of marker1 in current segment
            Marker2 = self.marker2_dict[key]    # Value of marker2 in current segment
            self.marker1 = np.concatenate((self.marker1,np.linspace(Marker1,Marker1,Length))) 
            self.marker2 = np.concatenate((self.marker2,np.linspace(Marker2,Marker2,Length)))

        self.unscaled_waveform = self.waveform # Buffer waveform to be scaled - in order to avoid multiple rescalings
        #self.rescaleAmplitude() # Resclaing amplitude for getting correct output on AWG
        
        
        
        
    def rescaleLength(self, inp_time):  # Function for rescaling length depending on AWG period and selected time units
        self.AWG_period = 1.0/self.AWG_clock
        Length = int(inp_time*self.TimeUnits/self.AWG_period)   # Changed 09.03_13:31
        if Length < 5:                                          # Changed 09.03_13:31
            raise Exception('AWG sampling rate too small')    # Changed 09.03_13:31
        return Length
        
    def rescaleAmplitude(self, AWGMaxAmp):
        self.waveform = self.unscaled_waveform*self.AmpUnits
        # Converting from selected units to V
        #self.Max_amp = max(self.waveform)         # Saving Max_amp to be able to set the AWG
        self.waveform = self.waveform/AWGMaxAmp     # Scaling
        self.waveform = self.waveform - np.mean(self.waveform)   # Substracting mean value in order not to heat up the fridge
    
    def InverseHPfilter(self, R,C, F_sample = 10000000, M=None):
        """Filtering on a real signal using inverse FFT
        
        Inputs
        =======
        
        X: 1-D numpy array of floats, the real time domain signal (time series) to be filtered
          
        
        Notes
        =====
        1. The input signal must be real, not imaginary nor complex
        2. The Filtered_signal will have only half of original amplitude. Use abs() to restore. 
        
        
        """        
        
        
        import scipy, numpy, cmath
        import matplotlib.pyplot as plt
        
        X = self.waveform
        if M == None: # if the number of points for FFT is not specified
            M = X.size # let M be the length of the time series
        Spectrum = scipy.fft(X, n=M) 
        
        #plt.figure("Spectrum_real")
        #plt.plot(scipy.real(Spectrum))
        #plt.plot(scipy.imag(Spectrum))
        
        
        """
        Generating a transfer function for RC filters.
        Importing modules for complex math and plotting.
        """
    
        f = numpy.arange(-len(Spectrum)/2,len(Spectrum)/2, 1)
        w = 2.0j*numpy.pi*f
    
    
        
        hp_tf = (w*R*C)/(w*R*C+1)  # High Pass Transfer function
        
    
    
        
        right_hp_tf = hp_tf[len(hp_tf)/2:len(hp_tf)]
        right_hp_tf_inv = 1/right_hp_tf[1:len(right_hp_tf)]
        #print("right_hp_tf:  ", len(right_hp_tf))
        #print("right_hp_tf_inv:  ", len(right_hp_tf_inv))
        left_hp_tf = hp_tf[0:len(hp_tf)/2]
        left_hp_tf_inv = 1/left_hp_tf
        #print("left_hp_tf:  ", len(left_hp_tf))
        #print("left_hp_tf_inv:  ", len(left_hp_tf_inv))
        
        
        hp_tf = numpy.concatenate((right_hp_tf,left_hp_tf))
        inv_hp_tf = numpy.concatenate((np.array([0]),right_hp_tf_inv,left_hp_tf_inv))
        #print("inv_hp_tf:  ", len(inv_hp_tf))
        
        #plt.figure("RC_real")
        #plt.plot(f, scipy.real((hp_tf))) # plot high pass transfer function
        #plt.figure("RC_imag")
        #plt.plot(f, scipy.imag(hp_tf)) # plot high pass transfer function
        
        
        
        
    
    
        #plt.figure("RCinv_real")
        #plt.plot(f, scipy.real((inv_hp_tf))) # plot high pass transfer function
        #plt.figure("RCinv_imag")
        #plt.plot(f, scipy.imag(inv_hp_tf)) # plot high pass transfer function
        
        #plt.show()
    
    
    
        #Filtered_spectrum = Spectrum*hp_tf  # Filtering with HP
        #Filtered_spectrum = Filtered_spectrum*inv_hp_tf  # Filtering with inverse HP afterwards
        Filtered_spectrum = Spectrum*inv_hp_tf # Filtering with inverse HP
        
        
        #print("Filtered_spectrum:  ", len(Filtered_spectrum))
        
        
        
        
        Filtered_signal = scipy.ifft(Filtered_spectrum, n=M)  # Construct filtered signal
        plt.figure("Inv_Filtered_signal")
        plt.plot(Filtered_signal) 
        plt.show() 
        
        self.waveform = Filtered_signal  
        
        
 
        
        
        
            
        
    def plotWaveform(self, Name = None):    # IN PROGRESS... 
        return    # Just to skip plotting                        # DELETE THIS LINE AFTER! 
        if type(Name) is str:    
            plt.figure(Name)
        else:
            plt.figure(self.waveform_name) 
        t = np.linspace(1, len(self.waveform),len(self.waveform))*self.AWG_period/self.TimeUnits   # Creating time axis
        plt.subplot(511)
        y = self.waveform*self.AmpUnits  
        plt.plot(t,y)       # Ploting waveform
        plt.ylabel('Waveform amplitude'  + '  ' + self.AmpUnitsKey)
        plt.xlabel('Waveform time in' + '  ' + self.TimeUnitsKey)
        plt.subplot(513)
        y = self.marker1
        plt.plot(t,y)       # Ploting marker 1
        plt.ylabel('Marker1 amplitude')
        plt.xlabel('Waveform time in' + '  ' + self.TimeUnitsKey)
        plt.subplot(515)
        y = self.marker2
        plt.plot(t,y)       # Ploting marker 2
        plt.ylabel('Marker2 amplitude')
        plt.xlabel('Waveform time in' + '  ' + self.TimeUnitsKey)
        plt.show(block=False)
        
        
    def sequence(self, p2, NumOfSteps, seqName):  # Ovo se ipak moze mozda izdojiti u zasebnu klasu 
        '''
        Creates new sequence based on strating (p1) and ending (p2) wavefroms. Amplitudes and timings are linear interpolated per segments between p1 and p2,
        while markers are just shifted from p1 markers to p2 markers in time. Markers do not change amplitudes in individual segments.  
        '''
        seq = list() # Empty list for new sequence
        if len(self.amplitudes) > 0 and (len(self.amplitudes) == len(p2.amplitudes)):  # If waveforms pstart and pend are set and have equal number of elements
            delta_time = (np.array(p2.timings.values()) - np.array(self.timings.values()))/float(NumOfSteps)  # Calculating timing step
            delta_amp = (np.array(p2.amplitudes.values()) - np.array(self.amplitudes.values()))/float(NumOfSteps)  # Calculating amplitude step
            #delta_marker1 = (np.array(p2.marker1_dict.values()) - np.array(self.marker1_dict.values()))  # Calculating marker1 change
            #delta_marker2 = (np.array(p2.marker2_dict.values()) - np.array(self.marker2_dict.values()))  # Calculating marker2 change
            
            for i in xrange(NumOfSteps):  # Creating each element in sequence as separate Pulse object
                seq.append(Pulse(waveform_name = self.waveform_name +'elem%d'%i, AWG_clock = self.AWG_clock, TimeUnits = self.TimeUnitsKey , AmpUnits = self.AmpUnitsKey))
                    
                for num,(key, item) in enumerate(self.timings.iteritems()):
                    seq[i].setTimings(**{key : item + i*delta_time[num]})
                       
                for num,(key, item) in enumerate(self.amplitudes.iteritems()):
                    seq[i].setAmplitudes(**{key : tuple(item + i*delta_amp[num])})
                    
                for num,(key, item) in enumerate(self.marker1_dict.iteritems()):
                    seq[i].setMarker1(**{key : item}) #+ delta_marker1[num]
                    
                for num,(key, item) in enumerate(self.marker2_dict.iteritems()):
                    seq[i].setMarker2(**{key : item}) #+ delta_marker2[num]
                    
                seq[i].plotWaveform(Name = self.waveform_name + seqName) 
                    
            return seq   # Sequence is returned as list of Pulse objects
 
        else: 
            
            print('Unable to create sequence - waveform for specified channel not defined')  
            
                    
        
                
                
                  
            
            
        
            
            

            
                                    
class Waveform():
         
    '''
    AWG5014C waveform class.
    
       Initialization parameters:
           
            waveform_name (string) : Name of the wavefrom. By this name it will be saved on AWG hard and imported in 
                                     AWG wavefrom list.
                                     
            AWG_clock (int) : Sampling rate (clock) of AWG. Needed for calculation of correct wavefrom length.
            
            TimeUnits (str) : Time units in {'us','ms','s'}
            
            AmpUnits (str) : Amplitude units in {'uV','mV','V'}
            
    '''
    
    def __init__(self, waveform_name = 'WAV1', AWG_clock = None, TimeUnits = 'us' , AmpUnits = 'mV'):
        
        if AWG_clock is None:
            raise Exception('Error: AWG_clcok is not passed')
        else:
            self.AWG_clock = AWG_clock
            self.AWG_period = 1/float(AWG_clock)     # Calculating AWG period
            
        self.TimeUnits = TimeUnits
        self.AmpUnits = AmpUnits
        
        
        self.waveform_name = waveform_name
        
        self.CH1=Pulse(waveform_name = self.waveform_name+'CH1', AWG_clock = self.AWG_clock, TimeUnits = self.TimeUnits , AmpUnits = self.AmpUnits)   # Changed 09.03_13:00
        self.CH2=Pulse(waveform_name = self.waveform_name+'CH2', AWG_clock = self.AWG_clock, TimeUnits = self.TimeUnits , AmpUnits = self.AmpUnits)   # Changed 09.03_13:00
        self.CH3=Pulse(waveform_name = self.waveform_name+'CH3', AWG_clock = self.AWG_clock, TimeUnits = self.TimeUnits , AmpUnits = self.AmpUnits)   # Changed 09.03_13:00
        self.CH4=Pulse(waveform_name = self.waveform_name+'CH4', AWG_clock = self.AWG_clock, TimeUnits = self.TimeUnits , AmpUnits = self.AmpUnits)   # Changed 09.03_13:00
                 
        self.lengthV = 0
        self.lengthM = 0
        
        
    def setAWG_clock(self, AWG_clock=1e8):    
        self.AWG_clock = AWG_clock
        self.AWG_period = 1/float(AWG_clock)     # Calculating AWG period
    
        self.CH1.setAWG_clock(self.AWG_clock)
        self.CH2.setAWG_clock(self.AWG_clock)
        self.CH3.setAWG_clock(self.AWG_clock)
        self.CH4.setAWG_clock(self.AWG_clock)

    
        
    def setValuesCH1(self, *args):    # Izbjegavati *args i *kwargs nego koristiti call specific strukture
        self.setValues(self.CH1,args)
               
    def setValuesCH2(self, *args):
        self.setValues(self.CH2,args)
        
    def setValuesCH3(self, *args): 
        self.setValues(self.CH3,args)
        
    def setValuesCH4(self, *args): 
        self.setValues(self.CH4,args)
        
         
    def setMarkersCH1(self, *args): 
        self.setMarker(self.CH1,args)
        
    def setMarkersCH2(self, *args): 
        self.setMarker(self.CH2,args)
        
    def setMarkersCH3(self, *args): 
        self.setMarker(self.CH3,args)
        
    def setMarkersCH4(self, *args): 
        self.setMarker(self.CH4,args)
        
    
    def rescaleAmplitude(self, AWGMaxAmp):
        self.CH1.rescaleAmplitude(AWGMaxAmp)
        self.CH2.rescaleAmplitude(AWGMaxAmp)
        self.CH3.rescaleAmplitude(AWGMaxAmp)
        self.CH4.rescaleAmplitude(AWGMaxAmp)

    def Change_time_units(self, new_unit):
        '''Function for on the fly changing the time units of the waveform
            Raises exception if time unit is not one of: us, ms, s'''
        if new_unit in self.CH1.TimeUnitsDict.keys():
            self.CH1.TimeUnitsKey = new_unit
            self.CH1.TimeUnits = self.CH1.TimeUnitsDict[new_unit]
            self.CH2.TimeUnitsKey = new_unit
            self.CH2.TimeUnits = self.CH1.TimeUnitsDict[new_unit]
            self.CH3.TimeUnitsKey = new_unit
            self.CH3.TimeUnits = self.CH1.TimeUnitsDict[new_unit]
            self.CH4.TimeUnitsKey = new_unit
            self.CH4.TimeUnits = self.CH1.TimeUnitsDict[new_unit]
        else:
            raise Exception("%s not a proper unit!"%new_unit)


    def Change_amp_units(self, new_unit):
        '''Function for on the fly changing the amplitude units of the waveform
            Raises exception if amp unit is not one of: uV, mV, V'''
        if new_unit in self.CH1.AmpUnitsDict.keys():
            self.CH1.AmpUnitsKey = new_unit   
            self.CH1.AmpUnits = self.CH1.AmpUnitsDict[new_unit]
            self.CH2.AmpUnitsKey = new_unit 
            self.CH2.AmpUnits = self.CH1.AmpUnitsDict[new_unit]
            self.CH3.AmpUnitsKey = new_unit 
            self.CH3.AmpUnits = self.CH1.AmpUnitsDict[new_unit]
            self.CH4.AmpUnitsKey = new_unit 
            self.CH4.AmpUnits = self.CH1.AmpUnitsDict[new_unit]
        else:
            raise Exception("%s not a proper unit!"%new_unit)
        
    
           
     
        
                
    def setValues(self, pulse, values):
        '''TO DO''' # Check lengths of each input value
        # Danijelovi naputci: Promijeniti ovu funkciju tako da je ulaz lista u listi - jednostavnija dekompozicija i proslijedivanje, neovisnost izmedu klasa
        # - e.g. klasa waveform samo sve posalje klasi pulse, a ova to dalje hendla onda.
        buffer_dict_Amplitudes = dict()  
        buffer_dict_Timings = dict()  
        for count,item in enumerate(values):
            key = 'T%d'%count
    
            if len(item) < 2:
                raise Exception('Error: You need to specify timing and amplitude for all points')
            elif len(item) == 3:
                buffer_dict_Amplitudes[key] = (item[1],item[2])  # Creating amplitude chunk for ramp segment  
            else:
                buffer_dict_Amplitudes[key] = (item[1],item[1])  # Creating amplitude chunk for rect segment 
            buffer_dict_Timings[key] = (item[0])
            
        pulse.setTimings(**buffer_dict_Timings)    # Passing timing info to Pulse class (passed as dict)
        pulse.setAmplitudes(**buffer_dict_Amplitudes)    # Passing amplitude info to Pulse class (passed as dict)
        self.lengthV = len(buffer_dict_Timings)    # Synchronization 
        #if self.lengthV == self.lengthM:
            #pulse.plotWaveform()
        
        
            
            
            
    def setMarker(self,pulse, values):
        '''TO DO'''  # Check lengths of each input marker
        # Danijelovi naputci: Promijeniti ovu funkciju tako da je ulaz lista u listi - jednostavnija dekompozicija i proslijedivanje, neovisnost izmedu klasa
        # - e.g. klasa waveform samo sve posalje klasi pulse, a ova to dalje hendla onda.
        buffer_dict_Marker1 = dict()
        buffer_dict_Marker2 = dict()
        for i,item in enumerate(values):    # Items should be lists for m1 and m2
            
            for count, mark in enumerate(item):  # Going trough arguments of each list
                key = 'T%d'%count                # Key for marker1 and marker2 dictionaries
                if i == 0:     # If marker1
                    buffer_dict_Marker1[key] = int(bool(mark))     
                elif i == 1:   # If marker2
                    buffer_dict_Marker2[key] = int(bool(mark))         
                else:
                    raise Exception('Error in setting markers')
        pulse.setMarker1(**buffer_dict_Marker1) 
        pulse.setMarker2(**buffer_dict_Marker2)
        self.lengthM = len(buffer_dict_Marker2)    # Synchronization 
        #if self.lengthV == self.lengthM:
            #pulse.plotWaveform()
            
            
## SEQUENCES    
            
            
  
        
    def interpolate_toCH1(self,NumOfSteps, p2 = None, seqName = 'SEQ1'):
        '''
        Creates sequence for channel 1 - returns list of sequence waveform elements
        '''
        seq = self.CH1.sequence(p2.CH1, NumOfSteps, seqName)
        return(filter(None, seq))
        
    def interpolate_toCH2(self,NumOfSteps, p2 = None, seqName = 'SEQ1'):
        '''
        Creates sequence for channel 2 - returns list of sequence waveform elements
        '''
        seq = self.CH2.sequence(p2.CH2, NumOfSteps, seqName)
        return(filter(None, seq))
        
    def interpolate_toCH3(self,NumOfSteps, p2 = None, seqName = 'SEQ1'):
        '''
        Creates sequence for channel 3 - returns list of sequence waveform elements
        '''
        seq = self.CH3.sequence(p2.CH3, NumOfSteps, seqName)
        return(filter(None, seq))
        
    def interpolate_toCH4(self,NumOfSteps, p2 = None, seqName = 'SEQ1'):
        '''
        Creates sequence for channel 4 - returns list of sequence waveform elements
        '''
        seq = self.CH4.sequence(p2.CH4, NumOfSteps, seqName)
        return(filter(None, seq))
       
       
        
    def interpolate_to(self,NumOfSteps, p2 = None, seqName = 'SEQ1'):
        '''
        Creates sequence for all channels - returns list of lists of sequence waveform elements 
        '''
        seq = [self.CH1.sequence(p2.CH1, NumOfSteps, seqName), self.CH2.sequence(p2.CH2, NumOfSteps, seqName), self.CH3.sequence(p2.CH3, NumOfSteps, seqName), self.CH4.sequence(p2.CH4, NumOfSteps, seqName)]
        return(filter(None, seq))
        
        
        
    
  
        
            

            
            
            
    
            
            

        
                   
                         
            
            
            
            

        
        
         
    

        
        
    


            
            
            

        
        
        
         
        
        
          