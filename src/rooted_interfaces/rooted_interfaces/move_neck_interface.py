from rclpy.node import Node
from rooted_msgs.srv import NeckServo

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
        self.future = None

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