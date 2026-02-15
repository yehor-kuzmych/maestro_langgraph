#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from ast import literal_eval
from rooted_interfaces.rooted_interfaces.sensors_interface import SensorReader
from rooted_interfaces.rooted_interfaces.vision_interface import Cameras
from rooted_interfaces.rooted_interfaces.busy_interface import BusyInterface
from rclpy.action import ActionServer, ActionClient
from rooted_msgs.action import HighLevelAction
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Twist 
from tf2_ros import Buffer, TransformListener
from tf2_geometry_msgs import do_transform_pose


###############################################################################################
#    This portion of the code should be uncommented in case it is running in a ARM computer   #
###############################################################################################
# import sys
# sys.path.append('/home/plantroid/plantroid_ws/src/plantroid_navigation/plantroid_navigation')
#c = get_config()
#os.environ['LD_PRELOAD'] = '/usr/lib/aarch64-linux-gnu/libgomp.so.1'
#c.Spawner.env.update('LD_PRELOAD')
# import sys
# sys.path.insert(1, './OKAO')
# from movement_module.OKAO_vision_interface import get_image_array
###############################################################################################


class HighLevelNavigationActionServer(Node):
    """! Class that implements the node responsible for safely navigating the robot."""
    def __init__(self):
        """! High level Navigator Action Server node initializer method."""

        super().__init__('high_level_navigation_action_server')
        self.action_server = ActionServer(self, HighLevelAction, '/plantroid/high_level_navigation', self.execute_callback)
        self.move_base_client = ActionClient(self, NavigateToPose, '/plantroid/navigate_to_pose')
        self.feedback = HighLevelAction.Feedback()
        self.result = HighLevelAction.Result()
        
        self.cmd_vel_publisher = self.create_publisher(Twist, '/plantroid/cmd_vel', 10)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.camera_client = Cameras('high_lvl_nav_navigation_camera_service')
        self.busy_interface = BusyInterface('high_lvl_nav_busy_interface')
        self.image_history = []
        
    def get_person(self):
        """! Method responsible for detecting a person using the vision service.
        @return <bool/array>: Detection result or image data.
        """
        response = False
        self.camera_client.send_request(3)
        while rclpy.ok():
            rclpy.spin_once(self.camera_client)
            if self.camera_client.future.done():
                try:
                    response = self.camera_client.future.result().image
                except Exception as e:
                    self.camera_client.get_logger().info('Service call failed: %r' % (e,))
                else:
                    response = literal_eval(response)
                break
        return response

    def rotate_to_person(self):
        """! Method responsible for rotating the robot to face a detected person."""
        person = self.get_person()
        
        while not person:
            print("Seeking humans")
            person = self.get_person()
            self.publish_twist(0.0, 0.5)
        print("Person found!")

        for _ in range(4):
            self.publish_twist(0.0, 0.0)

    def send_goal_to_navigate_to_pose(self, command):
        x, y = self.camera_client.send_request(6 if command == 'light' else 7 )
        goal_pose_stamped = PoseStamped()
        goal_pose_stamped.header.frame_id = 'base_link'
        goal_pose_stamped.header.stamp = self.get_clock().now().to_msg()
        goal_pose_stamped.pose.position.x = x
        goal_pose_stamped.pose.position.y = y
        goal_pose_stamped.pose.position.z = 0.0
        goal_pose_stamped.pose.orientation.x = 0.0
        goal_pose_stamped.pose.orientation.y = 0.0
        goal_pose_stamped.pose.orientation.z = 0.0
        goal_pose_stamped.pose.orientation.w = 1.0

        transform = self.tf_buffer.lookup_transform('base_link', 'world', rclpy.time.Time())
        transformed_pose_stamped = do_transform_pose(goal_pose_stamped, transform)

        navigate_to_pose_goal = NavigateToPose.Goal()
        navigate_to_pose_goal.pose.header.frame_id = "base_link"
        navigate_to_pose_goal.pose.header.stamp = self.get_clock().now().to_msg()
        navigate_to_pose_goal.pose.pose = transformed_pose_stamped

        self.move_base_client.wait_for_server()
        self.move_base_client.send_goal_async(navigate_to_pose_goal, feedback_callback=self.navigate_to_pose_feedback_callback)
        self.result.result = "Task completed."

    def publish_twist(self, lin_spd, ang_spd):
        twist = Twist()
        twist.linear.x = float(lin_spd)
        twist.angular.z = float(ang_spd)
        self.cmd_vel_publisher.publish(twist)
    
    def set_idle(self):
        """! Method to set the robot's busy status to idle."""
        self.busy_interface.send_request(False)

    def set_busy(self):
        """! Method to set the robot's busy status to busy."""
        self.busy_interface.send_request(True)

    def check_busy(self):
        """! Method to check if the robot is currently busy.
        @return <bool>: True if busy, False otherwise.
        """
        if self.busy_interface.future.done():
            try:
                response = self.busy_interface.future.result()
            except Exception as e:
                self.camera_client.get_logger().info('Service call failed: %r' % (e,))
                return False
            else:
                return response.status

    def execute_callback(self, goal_handle):
        goal = goal_handle.request.command
        self.feedback.status = "Processing command: " + goal
        goal_handle.publish_feedback(self.feedback)
        
        if goal == "person":
            self.set_busy()
            self.rotate_to_person()
        else:
            self.send_goal_to_navigate_to_pose(goal)
        
        self.result.result = "Task completed."
        goal_handle.succeed()
        return self.result


def main(args=None):
    """! Main function that initializes the ROS node and keeps it running."""
    rclpy.init(args=args)
    navigator_node = HighLevelNavigationActionServer()
    rclpy.spin(navigator_node)
    navigator_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()