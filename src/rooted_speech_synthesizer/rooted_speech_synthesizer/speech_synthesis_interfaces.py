#!/usr/bin/env python3
import socket
import subprocess
from balacoon_tts import TTS, SpeechUtterance
from ast import literal_eval
import wave


def espeak_ng(msg):
    """!
    Synthesizes speech using the espeak-ng TTS engine, a lightweight option with lower quality.

    @param msg<str>: Input message containing the text to synthesize and TTS parameters.
                     Expects a serialized dictionary with:
                     - data[0]: The text to synthesize.
                     - data[1]: A tuple of (volume, speed, pitch).
    @return subprocess.Popen: The process running the espeak-ng synthesis command.
    """
    data = literal_eval(msg.data)
    speech_content = data[0]
    volume, speed, pitch = data[1]
    vlm, ptc, spd = ["-a", str(volume)], ['-p', str(pitch)], ['-s', str(speed)]
    cmd = ["espeak-ng"] + ["-v", "en-us+f3"] + ptc + vlm + spd + [speech_content]
    return subprocess.Popen(cmd)


def tortoise(msg):
    """!
    Synthesizes speech using the Tortoise TTS engine, a high-quality but resource-intensive option.
    @param msg<str>: Input message containing the text to synthesize.
    @note TODO: Implementation needed.
    """
    pass  # TODO: Implement Tortoise TTS synthesis


def tortoise_request(msg, IP=None, PORT=None):
    """!
    Sends a synthesis request to a remote Tortoise TTS server.

    @param msg<str>: Input message containing the text to synthesize.
    @param IP<str>: IP address of the remote server.
    @param PORT<int>: Port number of the remote server.
    @note TODO: Implementation needed.
    """
    pass  # TODO: Implement Tortoise remote request


def balacoon(msg):
    """!
    Synthesizes speech using the Balacoon TTS engine, a lightweight model suitable for edge devices.

    @param msg<str>: Input message containing the text to synthesize.
                     Expects a serialized dictionary or plain text:
                     - data[0]: The text to synthesize.
    @return subprocess.Popen: The process running the playback command for the synthesized audio.
    """
    data = msg.data
    speech = ""
    try:
        data = literal_eval(data)
        speech = data[0]
    except Exception as e:
        print(e)
        speech = data

    tts = TTS("/home/antoniogaliza/ResearchWork/rooted_sppech_synthesizer")
    supported_speakers = tts.get_speakers()
    speaker = supported_speakers[-1]
    samples = tts.synthesize(speech, speaker)
    with wave.open("speech.wav", "w") as fp:
        fp.setparams((1, 2, tts.get_sampling_rate(), len(samples), "NONE", "NONE"))
        fp.writeframes(samples)
    cmd = ["play", "speech.wav"]
    return subprocess.Popen(cmd)


def balacoon_request(msg, IP=None, PORT=None):
    """!
    Sends a synthesis request to a remote Balacoon TTS server.

    @param msg<str>: Input message containing the text to synthesize.
    @param IP<str>: IP address of the remote server.
    @param PORT<int>: Port number of the remote server.
    @note TODO: Implementation needed.
    """
    pass  # TODO: Implement Balacoon remote request


def tts_call(msg, mode="local", model="espeak_ng", IP=None, PORT=None):
    """!
    Calls the appropriate TTS engine based on the specified model and mode.

    @param msg<str>: Input message containing the text to synthesize.
    @param mode<str>: The mode of operation, either "local" or "remote". Default is "local".
    @param model<str>: The TTS engine to use ("espeak_ng", "tortoise", "balacoon"). Default is "espeak_ng".
    @param IP<str>: (Optional) IP address of the remote TTS server.
    @param PORT<int>: (Optional) Port number of the remote TTS server.
    """
    if model == "espeak-ng":
        process = espeak_ng(msg)
        process_done = process.poll() is None
        while process_done:
            process_done = process.poll() is None
        print("done")

    elif model == "tortoise":
        if mode == "local":
            tortoise(msg)
        else:
            tortoise_request(msg, IP, PORT)

    elif model == "balacoon":
        if mode == "local":
            process = balacoon(msg)
            process_done = process.poll() is None
            while process_done:
                process_done = process.poll() is None
            print("done")
        else:
            balacoon_request(msg, IP, PORT)

    else:
        pass
