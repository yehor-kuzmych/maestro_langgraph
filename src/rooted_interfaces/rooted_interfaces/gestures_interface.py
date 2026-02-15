from rclpy.node import Node
from rooted_msgs.srv import Gesture

class GestureRequests(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.cli = self.create_client(Gesture,"gesture")
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Sensor service not available, waiting again...')
        self.req = Gesture.Request()
        self.future = None

    def send_request(self, gesture):
        self.req.gesture = gesture
        self.future = self.cli.call_async(self.req)