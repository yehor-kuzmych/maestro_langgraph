from rclpy.node import Node
from rooted_msgs.srv import LLM

class TTSinterface(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.cli = self.create_client(LLM, 'tts_server')
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('TTS service not available, waiting again...')
        self.req = LLM.Request()
        self.req
        self.future = None

    def send_request(self, model, prompt):
        self.req.model = model
        self.req.prompt = prompt
        self.future = self.cli.call_async(self.req)