#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rooted_msgs.srv import Busy
from std_msgs.msg import String
from time import time


class BusyServer(Node):
    """!
    A ROS2 Node that provides a service to manage and notify the busy state of the system.
    """

    def __init__(self):
        """!
        Constructor for the BusyServer class.
        Initializes the service and publisher for managing the busy state.
        """
        super().__init__("busy_server")
        self.srv = self.create_service(Busy, "busy_service", self.handle_request)
        self.state = 0  ## Busy state of the system (0: idle, 1: busy)
        self.busy_notifier = self.create_publisher(String, 'busy_state_publisher', 10)

    def handle_request(self, req, resp):
        """!
        Callback for handling service requests to change or retrieve the busy state.

        @param req<Busy.Request>: The service request containing the command (set_busy or set_idle).
        @param resp<Busy.Response>: The service response to return the current state.
        @return Busy.Response: The response populated with the updated busy state.
        """
        data = req.request  ## Command received in the service request

        if data == "set_busy":
            self.state = 1
            notification = String()
            notification.data = str(self.state)
            self.busy_notifier.publish(notification)
        elif data == "set_idle":
            self.state = 0
            notification = String()
            notification.data = str(self.state)
            self.busy_notifier.publish(notification)

        resp.result = str(self.state)  ## Return the current state in the response
        return resp


def main():
    """!
    Entry point for the busy server application.
    Initializes the ROS2 node and starts spinning to handle requests.
    """
    rclpy.init(args=None)
    s = BusyServer()
    print("Ready to get busy.")
    rclpy.spin(s)
    # rclpy.shutdown()


if __name__ == "__main__":
    main()
