import AWG_lib
reload(AWG_lib)
import Waveform_PresetAmp as Wav
reload(Wav)
import numpy as np
#import qt
import matplotlib.pyplot as plt



### SETTING AWG
##
AWG_clock = 10e6        # Wanted AWG clock. Info https://www.google.at/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&ved=0ahUKEwjI5KCdy_TLAhXFuxQKHamZAHoQFggcMAA&url=http%3A%2F%2Fwww.tek.com%2Fdl%2F76W-19764-1.pdf&usg=AFQjCNGsPEYMv-JCA5vht2I1cSlzCVVVAA&sig2=RFFJuEw5rKO_uGo69H7U2A&cad=rja
											# In pdf on link read section "AWG: Simple Concept, Maximum Flexibility"
											
						# Take care about waveform and sequence length and clock rate  - AWG has limited capability
AWGMax_amp = 2          # In Volts!!! Maximum needed amplitude on all channels for your particular experiment (noise reduction) - need to be set at the beginning
Seq_length = 10      # Sequence length (number of periods - waveforms)
t_sync = 1              # Duration of synchronization element in sequence in "TimeUnits"
Automatic_sequence_generation = False   # Flag for determining type of sequence generation: Automatic - True,  Manual - False 


sync = Wav.Waveform(waveform_name = 'WAV1elem%d'%0, AWG_clock = AWG_clock, TimeUnits = 'ms' , AmpUnits = 'mV') # First element in sequence is synchronization element
#compensate = Wav.Waveform(waveform_name = 'WAV1elem%d'%1, AWG_clock = AWG_clock, TimeUnits = 'ms' , AmpUnits = 'mV') # Second element in sequence is element for substracting mean value



# Here was automatic sequence generation - look for it in previous verisons




#### MANUAL sequence generation - sequnce is generated manually - more flexible
if not(Automatic_sequence_generation):  # If user wants manual sequence generation (Automatic_sequence_generation = False)

    seqCH1 = list() # Initializing list for channel 1 sequence
    seqCH2 = list()	# Initializing list for channel 2 sequence
    seq = list() # Initializing list that will contain all sequences (all channels)


    A1 = np.array([0.0,2,0.0,0.0,0.0])*31.25 # Initial amplitudes, 31.25 is factor of attenuation
    delta_A1 = -3.0*31.25/(Seq_length/1.0) 
    #delta_A1 = (1+1.0/Seq_length)*delta_A1
    A2 = np.array([0.0,2,0.0,0.0,0.0])*31.25*0.81 # Initial amplitudes, 31.25 is factor of attenuation, 1.2 is factor for diagonal pulsing
    delta_A2 = (3.0*31.25*0.81)/(Seq_length/1.0)  

    #delta_A2 = (1+1.0/Seq_length)*delta_A2

    

    for i in xrange(Seq_length):   # Creating waveforms for all sequence elements
        p = Wav.Waveform(waveform_name = 'WAV1elem%d'%(i+1), AWG_clock = AWG_clock, TimeUnits = 'ms' , AmpUnits = 'mV')  # Generating next object wavefrom in sequnce
                                                                                                                         # Starting from second element (WAV1elem%d'%(i+1)) 
                                                                                                                         # because sync element is first 
        
        #if i == 0:
            #p.setValuesCH1([2,0])  # Starting element in sequence with zero amp for synchronization reasons
            #p.setMarkersCH1([0],[0])   # Starting element in sequence with zero marker amp for synchronization reasons
        #else:

        p.setValuesCH1([0.1, A1[0]],[0.1, A1[1]], [0.2,A1[2]], [0.2,A1[3]],[0.1,A1[4]]) # Setting waveform shape for one wavefrom object p in sequence seq for AWG channel 1 - [Time1,Amp1],[Time2,Amp2]...  Time in TimeUnits and Amp in AmpUnits
        p.setMarkersCH1([0,1,0,0,0],[0,1,0,0,0])  # Setting marker just in the first wavefrom of the sequence (further is zero)
        A1[2] = A1[2] - delta_A1 # Defining amplitude change between wavefroms in sequence


        
        #if i == 0:
            
            #p.setValuesCH2([2,0])  # Starting element in sequence with zero amp for synchronization reasons
            #p.setMarkersCH2([0],[0])   # Starting element in sequence with zero marker amp for synchronization reasons
        #else:

        p.setValuesCH2([0.1, A2[0]],[0.1, A2[1]], [0.2,A2[2]], [0.2,A2[3]],[0.1,A2[4]]) # Setting waveform shape for one wavefrom object p in sequence seq for AWG channel 1 - [Time1,Amp1],[Time2,Amp2]...  Time in TimeUnits and Amp in AmpUnits
        p.setMarkersCH2([0,1,0,0,0],[0,1,0,0,0])  # Setting marker just in the first wavefrom of the sequence (further is zero)
        A2[2] = A2[2] - delta_A2 # Defining amplitude change between wavefroms in sequence

    

    
        seqCH1.append(p.CH1) # Filing sequence list for channel 1 (seqCH1) with next waveform (period)
        seqCH2.append(p.CH2) # Filing sequence list for channel 2 (seqCH2) with next waveform (period)
    

    seq.append(seqCH1) # Putting sequence list for channel 1 in list that contain all sequences (all channels)
    seq.append(seqCH2) # Putting sequence list for channel 2 in list that contain all sequences (all channels)



    AWG_lib.set_waveform(seq,AWG_clock,AWGMax_amp, t_sync, sync) # Function for uploading and setting all sequence waveforms to AWG 
    
    raw_input("Press Enter if uploading to AWG is finished")