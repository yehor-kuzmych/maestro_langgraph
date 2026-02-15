#!/usr/bin/env python3
from __future__ import print_function

import rclpy
from rclpy.node import Node
from rooted_msgs.srv import NeckServo
from time import time
from rcl_interfaces.msg import ParameterDescriptor


class FakeServo:
    """!
    Simulated servo class for testing outside of Raspberry Pi hardware.
    """
    def __init__(self, pin, initial_pwm):
        """!
        Constructor for the FakeServo class.

        @param pin<int>: The GPIO pin to simulate.
        @param initial_pwm<int>: The initial PWM value for the fake servo.
        """
        self.PIN = pin  ## GPIO pin used for the fake servo
        self.pwm = initial_pwm  ## Initial PWM value

    def ChangeDutyCycle(self, pwm):
        """!
        Simulates changing the duty cycle of the servo.

        @param pwm<int>: The new PWM value to simulate.
        """
        self.pwm = pwm
        pos_dict = {1: 0, 2: 18, 3: 36, 4: 54, 5: 72, 6: 90, 7: 108, 8: 126, 9: 144,
                    10: 162, 11: 180}
        print("Fake servo on pin " + str(self.PIN) + " moving to " +
              str(pos_dict[pwm]) + " degrees.")


class NeckServoServer(Node):
    """!
    ROS2 Node providing a service to control a neck servo.
    """
    def __init__(self):
        """!
        Constructor for the NeckServoServer class.
        Initializes the ROS2 node, sets up the servo controller, and declares parameters.
        """
        super().__init__("neck_servo_service")
        self.srv = self.create_service(NeckServo, "neck_servo", self.handle_neck_servo)
        self.servoPIN = 17  ## GPIO pin for the servo

        raspi_descriptor = ParameterDescriptor(
            description='Variable that represents whether the code is running on a Raspberry Pi or not.'
        )
        self.declare_parameter('raspi', '', raspi_descriptor)
        self.raspi = self.get_parameter('raspi').value  ## Indicates if running on Raspberry Pi

        if self.raspi:
            try:
                import RPi.GPIO as GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.servoPIN, GPIO.OUT)
                self.controller = GPIO.PWM(self.servoPIN, 50)
                self.controller.start(0)
            except:
                self.controller = FakeServo(self.servoPIN, 50)
        else:
            self.controller = FakeServo(self.servoPIN, 50)

    def handle_neck_servo(self, req, resp):
        """!
        Callback for handling neck servo requests.

        @param req<NeckServo.Request>: The service request containing the desired angle.
        @param resp<NeckServo.Response>: The service response to be populated.
        @return NeckServo.Response: The response with the status of the operation.
        """
        angle = req.angle  ## Desired servo angle from the request
        if angle <= 10:
            self.controller.ChangeDutyCycle(angle)
            resp.status = "Tilted head to " + str(angle)
        else:
            initial = 4
            final = 3
            angle = initial
            while angle > final:
                angle -= 0.2
                t0 = time()
                self.controller.ChangeDutyCycle(angle)
                while time() - t0 < 0.25:
                    pass
            while angle < initial:
                angle += 0.2
                t0 = time()
                self.controller.ChangeDutyCycle(angle)
                while time() - t0 < 0.25:
                    pass
            self.controller.ChangeDutyCycle(5)
        print("Tilted head to " + str(angle))
        return resp


def main():
    """!
    Entry point for the neck servo service node.
    """
    rclpy.init(args=None)
    s = NeckServoServer()
    print("Ready to tilt head.")
    rclpy.spin(s)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
