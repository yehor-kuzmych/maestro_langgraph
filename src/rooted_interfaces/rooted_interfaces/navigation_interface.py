from rclpy.node import Node
from rclpy.action import ActionClient
from rooted_msgs.action import HighLevelAction

class NavigationCommandSender(Node):
    """! Class responsible for sending navigation commands to the robot."""
    def __init__(self, node_name):
        """! NavigationCommandSender class' initializer method."""
        super().__init__(node_name)
        self.action_client = ActionClient(self, HighLevelAction, '/plantroid/high_level_navigation')
        while not self.action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().info('Action server not available, waiting again...')

    def send_move_order(self, order):
        """! Sends a navigation command to move the robot.
        @param order <str>: Either 'light' or 'shadow' to move the robot accordingly."""
        if order in ["light", "shadow"]:
            goal_msg = HighLevelAction.Goal()
            goal_msg.command = order
            self.action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)
        else:
            self.get_logger().error("Illegal order; orders should be either 'light' or 'shadow'!")

    def feedback_callback(self, feedback_msg):
        self.get_logger().info(f"Received feedback: {feedback_msg.feedback.status}")
