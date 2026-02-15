#!/usr/bin/env python3
"""
A module for keyword recognition and speech synthesis. This script provides
functions for calibrating microphone noise, speaking with prosody parameters,
and obtaining a keyword through speech recognition.
"""

import speech_recognition as sr
from listening_module.audio import record_to_file, recognize_file, record
import subprocess

def noise_calibration(microphone, recognizer):
    """!
    Calibrate the recognizer for ambient noise using the provided microphone.
    
    @param microphone<sr.Microphone>: The microphone object used for audio input.
    @param recognizer<sr.Recognizer>: The recognizer object for speech recognition.
    """
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)


def speak(phrase, prosody_parameters=[100, 150, 90]):
    """!
    Speak a given phrase using the espeak voice engine with configurable prosody parameters.
    
    @param phrase<string>: The phrase to be spoken.
    @param prosody_parameters<list>: A list of prosody parameters [volume, speed, pitch].
        - volume<int>: Volume level (default is 100).
        - speed<int>: Speed of speech in words per minute (default is 150).
        - pitch<int>: Pitch level (default is 90).
    
    @return bool: True if the speech command was executed successfully.
    """
    print("Speak function called")
    ## list containing the selected voicce engine for subprocess command.
    voice_engine = ['espeak']
    volume, speed, pitch = prosody_parameters
    vlm, ptc, spd = ["-a", str(volume)], ['-p', str(pitch)], ['-s', str(speed)]
    ## list command for subprocess 
    cmd = voice_engine + ptc + vlm + spd + [phrase]
    ## subprocess
    c = subprocess.Popen(cmd)
    c.wait()
    return True


def keyword_obtention():
    """!
    Obtain a keyword by prompting the user to say their name twice consecutively.
    
    @return string: The recognized name if spoken twice consecutively.
    """
    ## robot name as understood by the speech to text system.
    name = None
    ## counter of how many times the user has taught the robot name.
    count = 0
    ## Phrase that the robot says in order to prompt users to teach its name.
    phrase = "Please, say my name!"
    r = sr.Recognizer()
    m = sr.Microphone()

    while True:
        speak(phrase)
        record_to_file("myname.wav")
        ## Name recognized by the voice to text engine. 
        name_rec = recognize_file("myname.wav")
        if count == 0:
            name = name_rec
            count = 1
            phrase = "Please, say my name once again!"
        else:
            if name_rec == name:
                count += 1
            else:
                count = 0
            if count == 2:
                return name
