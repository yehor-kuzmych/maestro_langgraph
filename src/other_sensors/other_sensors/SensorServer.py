#!/usr/bin/env python3
from __future__ import print_function
import rclpy
from rclpy.node import Node
from plantroid_msgs.srv import Sensors
import serial
from pymodbus.client import ModbusSerialClient


class SensorServer(Node):
    """!
    ROS2 node for handling sensor service requests.
    Initializes serial communication with soil and Arduino sensors
    and responds to client requests for sensor readings.
    """

    def __init__(self):
        """!
        Initializes the SensorServer node, declares parameters, and sets up serial connections.
        """
        super().__init__("sensor_service")
        self.srv = self.create_service(Sensors, "sensors_server",
                                       self.cb_function)

        soil_sensor_parameter_descriptor = ParameterDescriptor(
            description='Device path for the integrated smart soil sensor.'
        )
        self.declare_parameter('soil_sensor_path', '', soil_sensor_parameter_descriptor)
        self.NPK_port = self.get_parameter('soil_sensor_path').value

        arduino_parameter_descriptor = ParameterDescriptor(
            description='Device path for the Arduino sensor.'
        )
        self.declare_parameter('arduino_path', '', arduino_parameter_descriptor)
        self.arduino_port = self.get_parameter('arduino_path').value
        self.arduino = serial.Serial(self.arduino_port, 9600, timeout=5)
        self.NPK_sensor = serial.Serial(self.NPK_port, 9600, timeout=5)

    def cb_function(self, req, resp):
        """!
        Callback function to process sensor service requests.

        @param req<Sensors.Request>: The incoming service request.
        @param resp<Sensors.Response>: The outgoing service response.
        @return Sensors.Response: The populated response object with sensor readings.
        """
        sensor = req.sensor_number
        if sensor <= 5:
            resp.sensor_reading = self.get_arduino(str.encode(str(sensor)))
        elif sensor == 6:
            resp.sensor_reading = self.get_NPK("EC")
        elif sensor == 7:
            resp.sensor_reading = self.get_NPK("pH")
        elif sensor == 8:
            resp.sensor_reading = self.get_NPK("N")
        elif sensor == 9:
            resp.sensor_reading = self.get_NPK("P")
        elif sensor == 10:
            resp.sensor_reading = self.get_NPK("K")
        else:
            resp.sensor_reading = "0"
        return resp

    def get_arduino(self, sensor):
        """!
        Sends a request to the Arduino and reads the sensor response.

        @param sensor<bytes>: A string containing the sensor number encoded
        in bytes to be sent to the Arduino.
        @return str: The sensor reading from the Arduino.
        """
        self.arduino.write(sensor)
        return self.arduino.readline().decode("utf-8")[:-1]

    def get_NPK(self, value):
        """!
        Retrieves soil sensor readings via Modbus communication.

        @param value<str>: The type of soil data to retrieve (e.g., "EC", "pH", "N", "P", "K").
        @return str: The sensor reading for the specified value.
        """
        response = ""
        client = ModbusSerialClient(self.NPK_port, baudrate=9600)
        client.connect()
        while response == "":
            response = str(client.read_holding_registers(address={"EC": 0x0202,
                                                                  "pH": 0x0203,
                                                                  "N": 0x0204,
                                                                  "P": 0x0205,
                                                                  "K": 0x0206}[value],
                                                         count=1,
                                                         slave=1).registers[0])
        client.close()
        return response


def main():
    """!
    Main function to initialize and spin the SensorServer node.
    """
    rclpy.init(args=None)
    s = SensorServer()
    print("Ready to read sensors")
    rclpy.spin(s)
    rclpy.shutdown()


if __name__ == "__main__":
    main()