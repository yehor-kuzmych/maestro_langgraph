from rclpy.node import Node
from rooted_msgs.srv import Sensors


class SensorReader(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.cli = self.create_client(Sensors, 'sensors_server')
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Sensor service not available, waiting again...')
        self.req = Sensors.Request()
        self.future = None

    def send_request(self, num):
        self.req.sensor_number = num
        self.future = self.cli.call_async(self.req)