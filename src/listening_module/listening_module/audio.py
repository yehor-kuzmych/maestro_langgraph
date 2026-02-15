#!/usr/bin/env python3
"""
A module for audio recording and processing, including functionalities
for recording, normalizing, trimming, adding silence, and recognizing speech
from an audio file.
"""

from sys import byteorder
from array import array
from struct import pack
import pyaudio
import wave

## Threshold level for detecting silence
THRESHOLD = 1000

## Size of each audio chunk
CHUNK_SIZE = 1024

## Audio format (16-bit)
FORMAT = pyaudio.paInt16

## Audio sampling rate in Hz
RATE = 16000


def is_silent(snd_data):
    """!
    Determine if the given sound data is silent.
    
    @param snd_data<array>: The audio data as an array of signed shorts.
    @return bool: True if the maximum amplitude of the sound data is below the threshold.
    """
    return max(snd_data) < THRESHOLD


def normalize(snd_data):
    """!
    Normalize the volume of the given sound data.
    
    @param snd_data<array>: The audio data as an array of signed shorts.
    @return array: The normalized audio data.
    """
    MAXIMUM = 16384
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r


def trim(snd_data):
    """!
    Remove silence from the start and end of the sound data.
    
    @param snd_data<array>: The audio data as an array of signed shorts.
    @return array: The trimmed audio data.
    """
    def _trim(snd_data):
        snd_started = False
        r = array('h')
        for i in snd_data:
            if not snd_started and abs(i) > THRESHOLD:
                snd_started = True
                r.append(i)
            elif snd_started:
                r.append(i)
        return r

    snd_data = _trim(snd_data)
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data


def add_silence(snd_data, seconds):
    """!
    Add silence to the start and end of the sound data.
    
    @param snd_data<array>: The audio data as an array of signed shorts.
    @param seconds<float>: Duration of silence to add in seconds.
    @return array: The audio data with added silence.
    """
    silence = [0] * int(seconds * RATE)
    r = array('h', silence)
    r.extend(snd_data)
    r.extend(silence)
    return r


def record():
    """!
    Record audio from the microphone and return the normalized, trimmed data.
    
    @return tuple: A tuple containing the sample width and the audio data as an array.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
                    input=True, output=True,
                    frames_per_buffer=CHUNK_SIZE)
    ## Number of silent parts 
    num_silent = 0
    ## Variable that tells whether sound has started or not 
    snd_started = False

    r = array('h')

    while True:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        ## holds whether theaudio portion is silent or not.
        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True
        else:
            num_silent = 0

        if snd_started and num_silent > 50:
            break

    ## width of the audio sample
    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()
    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r


def record_to_file(path):
    """!
    Record audio from the microphone and save it to a file.
    
    @param path<string>: The file path to save the recorded audio.
    """
    sample_width, data = record()
    data = pack('<' + ('h' * len(data)), *data)
    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()


def recognize_file(filename):
    """!
    Recognize speech from an audio file using a speech recognition engine.
    
    @param filename<string>: Path to the audio file to process.
    @return string: Recognized text or an empty string if recognition fails.
    """
    import speech_recognition as sr
    r = sr.Recognizer()
    try:
        with sr.AudioFile(filename) as source:
            audio_data = r.record(source)
            text = r.recognize_sphinx(audio_data, language='en-US')
            return text
    except:
        return ""
