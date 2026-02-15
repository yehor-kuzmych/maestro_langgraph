from rclpy.node import Node
from rooted_msgs.srv import Camera, Busy, LLM, Sensors, MemoryRequest
from rclpy.action import ActionClient
from rooted_msgs.action import HighLevelAction

class BusyInterface(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.cli = self.create_client(Busy, 'busy_servive')
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Busy service not available, waiting again...')
        self.req = Busy.Request()
        self.future = None

    def send_request(self, busy):
        self.req.request = busy
        self.future = self.cli.call_async(self.req)