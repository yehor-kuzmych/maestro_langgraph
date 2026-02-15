#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from move_base_msgs.action import MoveBase
from std_msgs.msg import String
from rooted_msgs.srv import Busy, Camera

from math import sqrt, atan2
import numpy as np
from ast import literal_eval
import cv2
from time import time
from movement_module.NeuralNav import NeuralNavigation, NeuralNavigationH5
from geometry_msgs.msg import PoseStamped, Twist
from tf2_ros import Buffer, TransformListener
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose

from rooted_interfaces.rooted_interfaces.sensors_interface import SensorReader
from rooted_interfaces.rooted_interfaces.vision_interface import Cameras
from rooted_interfaces.rooted_interfaces.busy_interface import BusyInterface

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


def min_mag(x1, x2):
    """! Function that selects which number has the smallest absolute value.
    @param x1 <int/float>: First number to have its magnitude compared.
    @param x2 <int/float>: Second number to have its magnitude compared.
    @return <int/float>: x1 or x2, whichever has the smallest magnitude.
    """
    if abs(x1) <= abs(x2):
        return x1
    return x2


def interval(x1, x2):
    """! Function that accurately calculates the difference between two angle values between -180 and 180.
    @param x1 <int/float>: First angle in radians.
    @param x2 <int/float>: Second angle in radians.
    @return <int/float>: Difference between angles.
    """
    if x2 - x1 > np.pi:
        return (x2 - x1) - 2 * np.pi
    elif x2 - x1 < -np.pi: 
        return 2 * np.pi + (x2 - x1)
    else:
        return x2 - x1


class NavigatorNode(Node):
    def __init__(self):
        super().__init__('navigator_node')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.busy_interface = BusyInterface('movement_busy_interface')
        self.camera_client = Cameras("movement_camera_interface")
        self.goal = None
        self.goal_theta = None
        self.cmd_vel_publisher = self.create_publisher(Twist, '/plantroid/cmd_vel', 10)
        self.image_history = [cv2.resize(self.get_image(), (30, 40))]*15
        self.action_server = ActionServer(
            self,
            NavigateToPose,
            '/plantroid/navigate_to_pose',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )

    def goal_callback(self, goal_request):
        self.get_logger().info('Received goal request')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')
        feedback_msg = NavigateToPose.Feedback()
        result = NavigateToPose.Result()

        goal_pose = goal_handle.request.target_pose.pose
        self.goal = [goal_pose.position.x, goal_pose.position.y]
        self.goal_theta = atan2(goal_pose.orientation.z, goal_pose.orientation.w) * 2
        self.set_busy()

        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                self.get_logger().info('Goal canceled')
                goal_handle.canceled()
                self.publish_twist(0, 0)
                self.set_idle()
                return NavigateToPose.Result(status=GoalStatus.STATUS_CANCELED)

            try:
                trans = self.tf_buffer.lookup_transform('base_link', 'world', rclpy.time.Time())
                self.monitored_x = trans.transform.translation.x
                self.monitored_y = trans.transform.translation.y
                self.monitored_theta = trans.transform.rotation.z
            except Exception as e:
                self.get_logger().warn(f"Could not transform: {e}")
                return NavigateToPose.Result(status=GoalStatus.STATUS_CANCELED)

            error = sqrt((self.goal[0] - self.monitored_x) ** 2 + (self.goal[1] - self.monitored_y) ** 2)
            if abs(error) > 0.15:
                TVM = self.stitch10()
                NeuralNavigation(TVM, 
                                 self.monitored_theta,
                                 atan2(self.monitored_y-self.goal[1], self.monitored_x-self.goal[0]),
                                 error)
                error_theta = interval(self.monitored_theta, self.goal_theta)
                PI_lin, PI_rot = 1, 0.5
                rot_spd, lin_spd = error_theta, error * PI_lin
                self.publish_twist(min(0.15, lin_spd), rot_spd)  # Done in order to prevent accidents if the robot gets to fast

                feedback_msg.base_position = PoseStamped()
                feedback_msg.base_position.pose.position.x = self.monitored_x
                feedback_msg.base_position.pose.position.y = self.monitored_y
                feedback_msg.base_position.pose.orientation.z = self.monitored_theta
                goal_handle.publish_feedback(feedback_msg)
            else:
                self.goal = None
                self.goal_theta = None
                self.image_history = []
                self.set_idle()
                for _ in range(4):
                    self.publish_twist(0, 0)
                goal_handle.succeed()
                result.status = GoalStatus.STATUS_SUCCEEDED
                return result

    def stitch(self):
        """! Method that stitches a series of images into a larger image.
        @return <numpy.array>: Stitched image data.
        """
        stitched = []
        present_img = [self.get_image()]
        img_hist = self.image_history
        for current_image in present_img:
            height, width = 160, 120
            canvas = np.zeros((int(height), int(width)), dtype=np.float32)
            current_image = cv2.resize(current_image, (30, 40))
            current_image = np.squeeze(current_image)
            resized_previous_images = [current_image] + img_hist[:15]
            self.image_history = resized_previous_images[:15]
            for i in range(4):
                for j in range(4):
                    current_index = 4 * i + j
                    img = resized_previous_images[current_index]
                    for y in range(img.shape[0]):
                        for x in range(img.shape[1]):
                            canvas[y + img.shape[0] * i, x + img.shape[1] * j] = img[y, x]
            canvas = np.array(np.expand_dims(canvas, axis=-1))
            stitched.append(canvas)
        return stitched[0]

    def stitch10(self):
        """! Method that stitches a series of 10 images into a larger image.
        @return <numpy.array>: Stitched image data.
        """
        stitched = []
        present_img = [cv2.resize(self.get_image(), (120, 160))]
        img_hist = self.image_history
        height, width = 160, 120

        for current_image in present_img:
            canvas = np.zeros((200, 150), dtype=np.uint8)
            current_image = np.squeeze(current_image)
            canvas[0:height, 0:width] = current_image
            resized_previous_images = img_hist[:9]
            self.image_history = [cv2.resize(current_image, (30, 40))] + self.image_history[:14]

            for i in range(5):
                img = resized_previous_images[i]
                for y in range(img.shape[0]):
                    for x in range(img.shape[1]):
                        canvas[y + img.shape[0] * i, width + x] = img[y, x]
            resized_previous_images = resized_previous_images[::-1]
            
            for i in range(4):
                img = resized_previous_images[i]
                for y in range(img.shape[0]):
                    for x in range(img.shape[1]):
                        canvas[height + y, x + (img.shape[1] * i)] = img[y, x]

            canvas = np.array(np.expand_dims(canvas, axis=-1))
            stitched.append(canvas)
        return stitched[0]

    def get_image(self):
        """! Method responsible for capturing an image from the camera service.
        @return <numpy.array>: Image data captured from the camera service.
        """
        self.camera_client.send_request(1)
        while rclpy.ok():
            rclpy.spin_once(self.camera_client)
            if self.camera_client.future.done():
                try:
                    response = self.camera_client.future.result()
                except Exception as e:
                    self.camera_client.get_logger().info('Service call failed: %r' % (e,))
                else:
                    return literal_eval(response)

    def publish_twist(self, lin_spd, ang_spd):
        twist = Twist()
        twist.linear.x = float(lin_spd)
        twist.angular.z = float(ang_spd)
        self.cmd_vel_publisher.publish(twist)

    def set_idle(self):
        self.busy_interface.send_request(False)

    def set_busy(self):
        self.busy_interface.send_request(True)

def main(args=None):
    rclpy.init(args=args)
    navigator_node = NavigatorNode()
    rclpy.spin(navigator_node)
    navigator_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()