#!/usr/bin/env python3
from __future__ import print_function

import rclpy
from rclpy.node import Node
from rooted_msgs.srv import Sensors
from random import choice


class SensorServer(Node):
    """!
    ROS2 service node for providing sensor readings based on sensor numbers.
    
    This service returns simulated sensor readings for requested sensor numbers.
    """

    def __init__(self):
        """!
        Initialize the SensorServer node and create the service.
        
        The service is named "sensors_server" and uses the Sensors service type.
        """
        super().__init__("sensor_service")
        self.srv = self.create_service(Sensors, "sensors_server",
                                       self.cb_function)

    def cb_function(self, req, resp):
        """!
        Callback function for handling sensor requests.
        
        @param req<Sensors.Request>: The service request containing the sensor number.
        @param resp<Sensors.Response>: The service response to be populated with mockup random sensor readings.
        @return<Sensors.Response>: The populated service response.
        """
        sensor = req.sensor_number
        if sensor <= 5:
            if sensor == 3:
                resp.sensor_reading = str(32 + choice(range(-10, 5)))
            else:
                resp.sensor_reading = str(500 + choice(range(12, 47)))
        elif sensor == 6:
            resp.sensor_reading = str(10 + choice([0, 0, 0, 1, 1, 2, 3]))
        elif sensor == 7:
            resp.sensor_reading = str(73 + choice([0, 0, 0, 1, 1, 2, 3]))
        elif sensor == 8:
            resp.sensor_reading = str(100 + choice([0, 0, 0, 1, 1, 2, 3]))
        elif sensor == 9:
            resp.sensor_reading = str(124 + choice([0, 0, 0, 1, 1, 2, 3]))
        elif sensor == 10:
            resp.sensor_reading = str(112 + choice([0, 0, 0, 1, 1, 2, 3]))            
        else:
            resp.sensor_reading = "0"
        return resp

def main():
    """!
    Main entry point for the ROS2 node.
    
    Initializes the ROS2 system, creates the SensorServer node, and spins it to handle requests.
    """
    rclpy.init(args=None)
    s = SensorServer()
    print("Ready to read sensors")
    rclpy.spin(s)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
