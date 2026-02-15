from rclpy.node import Node
from rooted_msgs.srv import Camera

class Cameras(Node):
    def __init__(self, node_name):
        super().__init__(str(node_name))
        self.cli = self.create_client(Camera, 'camera')
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Camera service not available, waiting again...')
        self.req = Camera.Request()
        self.future = None

    def send_request(self, type):
        self.req.imagetype = type
        self.future = self.cli.call_async(self.req)