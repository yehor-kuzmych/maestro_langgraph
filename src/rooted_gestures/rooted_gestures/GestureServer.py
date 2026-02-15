#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rooted_msgs.srv import Gesture, Busy, NeckServo
from geometry_msgs.msg import Twist

from ast import literal_eval
from time import time


class BusyInterface(Node):
    """!
    A ROS2 client node for interacting with the busy state service.
    """

    def __init__(self):
        """!
        Constructor for the BusyInterface class.
        Initializes the client for the busy state service.
        """
        super().__init__('gesture_busy_check')
        self.cli = self.create_client(Busy, 'busy_service')
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Busy service not available, waiting again...')
        self.req = Busy.Request()

    def send_request(self, busy):
        """!
        Sends a request to the busy state service.

        @param busy<str>: The busy state command (e.g., "set_busy", "set_idle").
        """
        self.req.request = busy
        self.future = self.cli.call_async(self.req)


class NeckCommander(Node):
    """!
    A ROS2 client node for controlling the neck servo.
    """
    def __init__(self):
        """!
        Constructor for the NeckCommander class.
        Initializes the client for the neck servo service.
        """
        super().__init__('gesture_neck_servo')
        self.cli = self.create_client(NeckServo, 'neck_servo')
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Service not available, waiting again...')
        self.req = NeckServo.Request()

    def send_request(self, angle):
        """!
        Sends a command to the neck servo service to set the servo angle.

        @param angle<float>: The angle to set for the neck servo.
        """
        try:
            self.req.angle = float(angle)
            self.future = self.cli.call_async(self.req)
        except Exception as e:
            print(f"Error: {e}")


class GestureServer(Node):
    """!
    A ROS2 server node that handles gesture commands.
    """

    def __init__(self):
        """!
        Constructor for the GestureServer class.
        Initializes the gesture service, busy checker, and commanders.
        """
        super().__init__("gesture_server")
        self.srv = self.create_service(Gesture, "gesture", self.handle_gesture)
        self.busy_checker = BusyInterface()
        self.nc = NeckCommander()
        self.mc = self.create_publisher(Twist, '/plantroid/cmd_vel', 10)

    def handle_gesture(self, req, resp):
        """!
        Handles incoming gesture requests and executes the corresponding gestures.

        @param req<Gesture.Request>: The service request containing the gesture command.
        @param resp<Gesture.Response>: The service response to return the result.
        @return Gesture.Response: The response with the result of the gesture.
        """
        data = req.gesture
        if not self.check_busy():
            self.set_busy()
            if data == "bow":
                bow = 8
                while bow < 9:
                    self.nc.send_request(bow)
                    bow += 0.001
                t0 = time()
                while time() - t0 < 2:
                    pass
                while bow > 8:
                    self.nc.send_request(bow)
                    bow -= 0.001
                self.nc.send_request(0)

            elif data == "yes":
                for _ in range(3):
                    bow = 7
                    while bow < 9:
                        self.nc.send_request(bow)
                        bow += 0.005
                    while bow > 8:
                        self.nc.send_request(bow)
                        bow -= 0.05
                    self.nc.send_request(8)

            elif data == "no":
                for i in [0.5, -1, 0.5]:
                    t0 = time()
                    speed_command = Twist()
                    speed_command.linear.x, speed_command.angular.z = [0, i / abs(i) * 0.5]
                    self.mc.publish(speed_command)
                    while time() - t0 < abs(i):
                        pass

            elif data == "surprise":
                bow = 8
                while bow > 7:
                    self.nc.send_request(bow)
                    bow -= 0.01
                t0 = time()
                while time() - t0 < 2:
                    pass
                while bow < 8:
                    self.nc.send_request(bow)
                    bow += 0.001
                self.nc.send_request(0)
            self.set_idle()
        resp.result = "Done."
        return resp

    def busy_request(self, request):
        """!
        Sends a busy state request and waits for the response.

        @param request<str>: The busy state command.
        @return str: The result of the busy state request.
        """
        self.busy_checker.send_request(request)
        while rclpy.ok():
            rclpy.spin_once(self.busy_checker)
            if self.busy_checker.future.done():
                try:
                    return literal_eval(self.busy_checker.future.result().result)
                except Exception as e:
                    self.busy_checker.get_logger().info(f'Service call failed: {e}')

    def check_busy(self):
        """!
        Checks if the system is busy.

        @return bool: True if the system is busy, False otherwise.
        """
        return self.busy_request("get")

    def set_busy(self):
        """!
        Sets the system to a busy state.
        """
        self.busy_request("set_busy")

    def set_idle(self):
        """!
        Sets the system to an idle state.
        """
        self.busy_request("set_idle")


def main():
    """!
    Entry point for the gesture server application.
    Initializes the ROS2 node and starts spinning to handle gesture requests.
    """
    rclpy.init(args=None)
    s = GestureServer()
    print("Ready to make gestures.")
    rclpy.spin(s)


if __name__ == "__main__":
    main()
