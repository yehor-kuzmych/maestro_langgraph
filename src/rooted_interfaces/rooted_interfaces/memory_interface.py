from rclpy.node import Node
from rooted_msgs.srv import MemoryRequest

class MemoryAccess(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.cli = self.create_client(MemoryRequest, 'memory_reader')
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Memory service not available, waiting again...')
        self.req = MemoryRequest.Request()
        self.future = None

    def send_request(self, DB, command):
        self.req.db_name = DB
        self.req.command = command
        self.future = self.cli.call_async(self.req)