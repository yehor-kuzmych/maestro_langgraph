#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ast import literal_eval
from rooted_msgs.srv import LLM

import rooted_speech_synthesizer.speech_synthesis_interfaces as tts
from rcl_interfaces.msg import ParameterDescriptor


class SpeechSynthesisServer(Node):
    """!
    A ROS2 service node for handling text-to-speech (TTS) requests and publishing talking status.
    """

    def __init__(self, mode="local", IP="localhost", port=11434):
        """!
        Constructor for the SpeechSynthesisServer class.
        Initializes the TTS service, parameters, and a publisher for talking status.

        @param mode<str>: Specifies whether the TTS model runs locally or on a remote server. Default is "local".
        @param IP<str>: The IP address of the TTS server. Default is "localhost".
        @param port<int>: The port of the TTS service. Default is 11434.
        """
        super().__init__("tts_service")
        self.srv = self.create_service(LLM, "tts_server", self.cb_function)
        self.talking_status_publisher = self.create_publisher(String, 'IsTalkingTopic', 10)

        mode_descriptor = ParameterDescriptor(description='Whether the TTS model is running locally or on a remote server.')
        self.declare_parameter('mode', '', mode_descriptor)
        self.mode = self.get_parameter("mode").value

        ip_descriptor = ParameterDescriptor(description='IP address of the TTS server.')
        self.declare_parameter('IP', '', ip_descriptor)
        self.IP = self.get_parameter("IP").value

        port_descriptor = ParameterDescriptor(description='Port number of the TTS service.')
        self.declare_parameter('PORT', '', port_descriptor)
        self.port = self.get_parameter("PORT").value

    def cb_function(self, req, resp):
        """!
        Callback function to handle incoming TTS requests.

        @param req<LLM.Request>: The service request containing the TTS model and text to synthesize.
        @param resp<LLM.Response>: The service response indicating success or failure.
        @return LLM.Response: The response populated with the result of the TTS process.
        """
        model = req.model  ## The TTS model to use
        msg = req.prompt  ## The text to synthesize
        resp.response = "Success"
        try:
            talking_msg = String()
            talking_msg.data = "talking"
            self.talking_status_publisher.publish(talking_msg)

            tts.tts_call(msg, model, self.mode, self.IP, self.port)

            talking_msg.data = "silent"
            self.talking_status_publisher.publish(talking_msg)

        except Exception as e:
            self.get_logger().error(f"Error {str(e)} occurred.")
            resp.response = "Failure"

        return resp


def main():
    """!
    Entry point for the TTS server node application.
    Initializes the ROS2 node and starts spinning to handle TTS requests.
    """
    rclpy.init()
    TTS_server = SpeechSynthesisServer()
    rclpy.spin(TTS_server)


if __name__ == '__main__':
    main()
