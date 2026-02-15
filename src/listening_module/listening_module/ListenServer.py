#!/usr/bin/env python3
"""
A ROS2-based audio processing node that listens to speech, analyzes emotions, 
and publishes messages with audio metadata. Includes features for blocking listening, 
speech recognition, and emotion classification.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import speech_recognition as sr
import uuid
from time import time
import listening_module.VAD as vad
from transformers import pipeline
from rcl_interfaces.msg import ParameterDescriptor
from struct import pack

def save_audio(path, data):
    """!
    Save audio data to a specified file path.
    
    @param path<string>: The path where the audio file will be saved.
    @param data<sr.AudioData>: The audio data to save.
    """
    with open(path, "wb") as file:
        file.write(data.get_wav_data())
        file.close()

def voice_emotion_analysis(audio_file):
    """!
    Perform emotion analysis on the given audio file.
    
    @param audio_file<string>: Path to the audio file for emotion analysis.
    @return string: The estimated emotion from the audio.
    """
    classifier = pipeline("audio-classification", model="r-f/wav2vec-english-speech-emotion-recognition")
    prediction = classifier(audio_file, top_k=1)[0]  # TODO: Check if it is working well.  
    emotion_map = {"neutral": "neutral", "happy": "happy", "sad": "sad", 
                   "anger": "anger", "disgust": "anger", 
                   "surprise": "surprise", "fear": "surprise"}
    return emotion_map[prediction["label"].lower()]

class ListenServer(Node):
    """!
    A ROS2 Node for listening to speech, recognizing it, and publishing messages with metadata.
    """
    ## Class varible that controls whether 
    block = False
    ## language for the voice recognition engine.
    language = "en-US"
    
    def __init__(self):
        """!
        Initialize the ListenServer node and its parameters, publisher, and initial settings.
        """
        super().__init__('listener_server_node')
        my_parameter_descriptor = ParameterDescriptor(
            description='Location of the folder where the audio files of the speeches of users are stored.'
        )
        self.declare_parameter('audio_folder_path', '', my_parameter_descriptor)
        self.audio_path = self.get_parameter('audio_folder_path').value
        self.block_time = time()
        self.publisher = self.create_publisher(String, 'messageTopic', 10)

    def block_callback(self, message):
        """!
        Callback to toggle the blocking status of the listener.
        
        @param message<std_msgs.msg.String>: The message received to toggle blocking.
        """
        self.block = not self.block
        if self.block:
            self.block_time = time()
        self.get_logger().info("Changed Listening status to: " + str(not self.block))

    def listenCallback(self, recognizer, audio):
        """!
        Callback for processing recognized speech, saving audio, and publishing messages.
        
        @param recognizer<sr.Recognizer>: The speech recognizer instance.
        @param audio<sr.AudioData>: The audio data recognized.
        """
        if self.block:
            if time() - self.block_time > 15:
                self.block = not self.block
        else:
            print("Callback called")
            try:
                phrase = recognizer.recognize_google(audio, language=self.language)
                filename = str(uuid.uuid4())
                print("HEARD: " + phrase)
                save_audio(self.audio_path + filename, audio)
                emotion_estimate = voice_emotion_analysis(self.audio_path + filename)
                self.Publish(phrase.replace(";", ",") + ";" + filename + ";" + emotion_estimate)
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from recognition service; {e}")

    def start_listening(self, recognizer):
        """!
        Start listening to speech in the background.
        
        @param recognizer<sr.Recognizer>: The speech recognizer instance.
        @return function: The listener instance.
        """
        print("Starting Listening subprocess...")
        return recognizer.listen_in_background(recognizer, self.listenCallback)

    def stop_listening(self, listener):
        """!
        Stop the background listening process.
        
        @param listener<function>: The listener instance to stop.
        @return bool: True if successfully stopped; False otherwise.
        """
        print("Stopping Listening subprocess...")
        try:
            listener(wait_for_stop=False)
            print("Successfully stopped Listening subprocess.")
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return False

    def Publish(self, message):
        """!
        Publish a message to the ROS2 topic.
        
        @param message<string>: The message to be published.
        @return bool: True if successfully published; False otherwise.
        """
        print("Trying to publish: ", message)
        if not isinstance(message, str):
            message = str(message)
        try:
            ## ROS2 String message to be published.
            msg = String()
            msg.data = message
            self.publisher.publish(msg)
            self.get_logger().info("Published: " + message)
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return False

    def getBlock(self):
        """!
        Subscribe to the topic to receive commands for toggling listening status.
        """
        self.subscription = self.create_subscription(String, 'ListenBlockTopic', self.block_callback, 10)

def main():
    """!
    The main entry point for the ListenServer node.
    """
    rclpy.init(args=None)
    ## microphone 
    m = sr.Microphone()
    ## speech recognizer
    r = sr.Recognizer()
    vad.noise_calibration(m, r)

    ## listen_server object that will provide all related services.
    listen_server = ListenServer()
    listen_server.start_listening(r)
    listen_server.getBlock()
    rclpy.spin(listen_server)

if __name__ == "__main__":
    main()