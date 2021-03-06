'''
Created on May 7, 2015

@author: Butzik
'''

import os
import numpy as np
import array
from scipy.fftpack import rfft, irfft

from Logging import Logger

class AudioFilesPreprocessor(object):
    
    '''
    This class pre-process the audio files. 
    It removes silence from the beginning and the end of each file using SoX. (should be installed on your system)
    It also removes the original signal from the picked-up signal by subtracting them in the frequency domain.
    The results are saved in an np.array format in the folder specified in original_signal_substracted_path.
    '''
    silence_stripped_path = "Silence_stripped"
    original_signal_substracted_path = "Original_substracted"
    silence_configuration = {"below_period" : 1,
                             "override_duration": 0,
                             "threshold" : -29}

    
    def __init__(self, base_path, audio_files_configuration, original_sound_base_path, original_sound_file_name):
        self.base_path = base_path
        self.audio_configuration = audio_files_configuration
        self.original_sound_base_path = original_sound_base_path
        self.original_sound_file_name = original_sound_file_name
        self.maximal_signal_length = 0
        
    def strip_silence_from_file(self, base_path, file_name):
        file_absolute_path = os.path.join(base_path, file_name).replace(" ","\ ").replace("(", "\(").replace(")","\)")
        output_file = os.path.join(base_path, self.silence_stripped_path, file_name).replace(" ","\ ").replace("(", "\(").replace(")","\)")
        sox_command = "/usr/local/bin/sox -e %s -b%d -L -r%d -c1 %s %s " % (self.audio_configuration["encoding"],
                                                             self.audio_configuration["encoding_size"],
                                                             self.audio_configuration["sample_rate"],
                                                             file_absolute_path,
                                                             output_file)   
        silence_filter = "silence %d %d %s reverse silence %d %d %s reverse" % (self.silence_configuration["below_period"],
                                                                                self.silence_configuration["override_duration"],
                                                                                str(self.silence_configuration["threshold"]) + 'd',
                                                                                self.silence_configuration["below_period"],
                                                                                self.silence_configuration["override_duration"],
                                                                                str(self.silence_configuration["threshold"]) + 'd')
        Logger.log("AudioFilesPreprocessor: removing silence: %s" % (sox_command + silence_filter))
        Logger.log("AudioFilesPreprocessor: execution result: %s" % os.popen(sox_command + silence_filter).read())
        
    def strip_silence_from_entire_dataset(self):
        files = [self.strip_silence_from_file(self.base_path,file_name) for file_name in os.listdir(self.base_path) if (("DS" not in file_name) and (os.path.isfile(os.path.join(self.base_path,file_name))))]
        
        
    def get_signal_array_from_file(self, base_path, file_name):
        sound_file = open(os.path.join(base_path, file_name),"rb")
        sound_raw_buffer = sound_file.read()
        signal_array = np.array(array.array(self.audio_configuration["encoding_for_array"],sound_raw_buffer).tolist(), self.audio_configuration["encoding_dtype"])
        return signal_array
    
    def subtract_original_signal_from_picked_signal(self, original_signal, picked_signal):
        # Note this function assumes that the signals are aligned for the starting point!
        fft_length = max(len(original_signal), len(picked_signal))
        original_f_domain = rfft(original_signal, n= fft_length)
        picked_f_domain = rfft(picked_signal, n= fft_length)
        assert len(original_f_domain) == len(picked_f_domain)
        difference_signal = picked_f_domain - original_f_domain
        return irfft(difference_signal)
    
    def subtract_original_signal_from_dataset(self, original_signal_base_path, original_signal_file_name):
        self.strip_silence_from_file(original_signal_base_path, original_signal_file_name)
        self.original_signal = self.get_signal_array_from_file(os.path.join(original_signal_base_path,self.silence_stripped_path), original_signal_file_name)
        
        ## TDOD: REMOVE THIS!!!! ->
        self.original_signal = np.zeros(1)
        ## TDOD: REMOVE THIS!!!! <-
        
        files_list = [file_name for file_name in os.listdir(os.path.join(self.base_path,self.silence_stripped_path)) 
                      if (os.path.isfile(os.path.join(self.base_path,self.silence_stripped_path,file_name)) and ("DS" not in file_name))]    
        for file_name in files_list:
            Logger.log("AudioFilesPreprocessor: removing original sound: %s from: %s" % 
                         (os.path.join(original_signal_base_path,original_signal_file_name),file_name))
            signal = self.get_signal_array_from_file(os.path.join(self.base_path,self.silence_stripped_path), file_name)
            substracted_signal = self.subtract_original_signal_from_picked_signal(self.original_signal,signal)
            np.save(os.path.join(self.base_path,self.original_signal_substracted_path,file_name),substracted_signal)
            self.maximal_signal_length = max(self.maximal_signal_length, len(signal))
            
    def preprocess_dataset(self, strip_silence=True, subtract_original=True):
        if strip_silence: self.strip_silence_from_entire_dataset()
        if subtract_original: self.subtract_original_signal_from_dataset(self.original_sound_base_path, self.original_sound_file_name)
        Logger.log("AudioFilesPreprocessor:dataset preprocessed. Maximal signal length is %s " % self.maximal_signal_length)
        
    def preprocess_file(self, base_path, file_name, strip_silence=True, subtract_original=True):
        Logger.log("AudioFilesPreprocessor: preprocessing file: %s" % file_name)
        signal = self.get_signal_array_from_file(base_path, file_name)
        
        self.strip_silence_from_file(self.original_sound_base_path, self.original_sound_file_name)
        self.original_signal = self.get_signal_array_from_file(os.path.join(self.original_sound_base_path,self.silence_stripped_path), self.original_sound_file_name)
        ## TDOD: REMOVE THIS!!!! ->
        self.original_signal = np.zeros(1)
        ## TDOD: REMOVE THIS!!!! <-

        if strip_silence: self.strip_silence_from_file(base_path, file_name)
        if subtract_original: self.subtract_original_signal_from_picked_signal(self.original_signal,signal)
                    
