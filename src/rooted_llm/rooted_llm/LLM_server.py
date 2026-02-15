#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ast import literal_eval
from rooted_msgs.srv import LLM

import sys
from rcl_interfaces.msg import ParameterDescriptor

# Add the location of this package to the system path
sys.path.append('')
import rooted_llm.LLM_interfaces as llm


class LLMServer(Node):
    """!
    A ROS2 service node for interacting with a Language Model (LLM).
    """

    def __init__(self, mode="local", IP="localhost", port=11434):
        """!
        Constructor for the LLMServer class.
        Initializes the LLM service and sets up parameters for mode, IP, and port.

        @param mode<str>: Specifies whether the LLM runs locally or on a remote server. Default is "local".
        @param IP<str>: The IP address of the LLM server. Default is "localhost".
        @param port<int>: The port of the LLM service. Default is 11434.
        """
        super().__init__("llm_service")
        self.srv = self.create_service(LLM, "llm_server", self.cb_function)

        mode_descriptor = ParameterDescriptor(
            description='Specifies whether the LLM model is running locally or on a remote server.'
        )
        self.declare_parameter('mode', '', mode_descriptor)
        self.mode = self.get_parameter('mode').value

        ip_descriptor = ParameterDescriptor(
            description='IP address of the LLM server.'
        )
        self.declare_parameter('IP', '', ip_descriptor)
        self.IP = self.get_parameter('IP').value

        port_descriptor = ParameterDescriptor(
            description='Port number of the LLM service.'
        )
        self.declare_parameter('PORT', '', port_descriptor)
        self.port = self.get_parameter('PORT').value

    def cb_function(self, req, resp):
        """!
        Callback function to handle incoming requests to the LLM service.

        @param req<LLM.Request>: The service request containing the model and prompt.
        @param resp<LLM.Response>: The service response containing the LLM's output.
        @return LLM.Response: The response populated with the LLM's result.
        """
        model = req.model  # The model to use
        msg = req.prompt  # The input prompt

        if self.mode == "local":
            resp.response = llm.ollama_local(msg, model)
        else:
            resp.response = llm.ollama_server(msg, model=model, IP=self.IP, port=self.port)

        return resp


def main():
    """!
    Entry point for the LLM server node application.
    Initializes the ROS2 node and starts spinning to handle LLM service requests.
    """
    rclpy.init()
    LLM_server = LLMServer()
    rclpy.spin(LLM_server)


if __name__ == '__main__':
    main()
