#!/usr/bin/env python3
from time import time, sleep

import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped, Twist
import tf_transformations
from rooted_encoder.rkm import KinematicModel
import numpy as np
from rooted_encoder.Ax12 import Ax12
from nav_msgs.msg import Odometry

Ax12.DEVICENAME = '/dev/ttyUSB0'  # Change for the appropriate device name  # TODO: change to rosparam
Ax12.BAUDRATE = 1000000  # Change for the appropriate baud rate for your device  # TODO: change to rosparam
Ax12.connect()

def servo_setup(servo):
    """!
    Set up the servo by setting its angle limits and initial speed.

    @param servo<Ax12>: The servo to set up.
    """
    servo.set_cw_angle_limit(0)
    servo.set_ccw_angle_limit(0)
    servo.set_moving_speed(0)

LS = Ax12(1)
RS = Ax12(2)

servo_setup(LS)
servo_setup(RS)

LS.set_moving_speed(0)
RS.set_moving_speed(0)

def speed_command_convert(s, l=0):
    """!
    Convert speed command to the appropriate servo speed value.

    @param s<float>: The speed command.
    @param l<int>: Flag indicating left (1) or right (0) servo.
    @return<int>: The converted speed value.
    """
    if s == 0:
        return 0
    if l:
        if s < 0:
            return min(-s * 180 / np.pi * 1023 / 300, 1023)
        else:
            return min(2046, s * 180 / np.pi * 1023 / 300 + 1023)
    else:
        if s < 0:
            return min(2046, -s * 180 / np.pi * 1023 / 300 + 1023)
        else:
            return min(1023, s * 180 / np.pi * 1023 / 300)

class Encoder(Node):
    """!
    Encoder class for handling robot kinematics and servo control.
    """
    def __init__(self, robot_kinematic_model=KinematicModel(), motors=[LS, RS], timer=None):
        """!
        Constructor for the Encoder class.

        @param robot_kinematic_model<KinematicModel>: The kinematic model of the robot.
        @param motors<list>: List of servos controlling the robot.
        @param timer<float>: Initial timer value.
        """
        super().__init__('Encoder')
        
        self.tf_broadcaster = TransformBroadcaster(self)
        self.speed_command_subscription = self.create_subscription(
            Twist,
            '/plantroid/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.odom_publisher = self.create_publisher(Odometry, '/plantroid/odom', 10)

        self.pose_timer = self.create_timer(0.1, self.publish_pose)
        self.speed_timer = self.create_timer(2**0.5 / 10, self.publish_speed)
        self.command_timer = self.create_timer(5**0.5 / 10, self.issue_speed_command)

        self.rkm = robot_kinematic_model
        self.x = self.rkm.pose[0]  ## X position of the robot
        self.y = self.rkm.pose[1]  ## Y position of the robot
        self.theta = self.rkm.pose[2]  ## Orientation of the robot

        self.l_servo, self.r_servo = motors
        self.l_id = self.l_servo.get_id()
        self.r_id = self.r_servo.get_id()
        self.motor_angle_l = self.l_servo.get_present_position()
        self.motor_angle_r = self.r_servo.get_present_position()

        if timer is None:
            self.timer = time()
        else:
            self.timer = timer 

        self.speed_command_pile = []

    def cmd_vel_callback(self, msg):
        """!
        Callback function for handling incoming speed commands.

        @param msg<Twist>: The incoming speed command message.
        """
        lin_speed = msg.linear.x
        ang_speed = msg.angular.z

        self.get_logger().info(
            "Received speed: [" + str(lin_speed) + "," + str(ang_speed) + "]")

        left_servo_speed, right_servo_speed = self.rkm.convert_LinearAngular_to_LeftRight(lin_speed, ang_speed)
        left_servo_speed = speed_command_convert(left_servo_speed, 1)
        right_servo_speed = speed_command_convert(right_servo_speed, 0)        
        self.speed_command_pile.append([right_servo_speed, left_servo_speed])        

    def speed_convert_mx12w(self, v):
        """!
        Convert servo speed value to the appropriate range.

        @param v<int>: The servo speed value.
        @return<int>: The converted speed value.
        """
        return int(v % 1024)

    def issue_speed_command(self):
        """!
        Issue speed commands to the servos from the command pile.
        """
        if self.speed_command_pile:
            right_servo_speed, left_servo_speed = self.speed_command_pile.pop(0)
            self.l_servo.set_moving_speed(int(left_servo_speed))
            self.r_servo.set_moving_speed(int(right_servo_speed))

    def publish_pose(self):
        """!
        Publish the robot's pose and odometry.
        """
        speed_r = self.speed_convert_mx12w(self.r_servo.get_present_speed()) * 360 / 1023
        speed_l = self.speed_convert_mx12w(self.l_servo.get_present_speed()) * 360 / 1023

        dt = time() - self.timer
        self.timer = time()
        self.rkm.left_speed = speed_l  ## Left wheel speed
        self.rkm.right_speed = speed_r  ## Right wheel speed
        self.rkm.update(dt)

        pose = {"x": self.rkm.pose[0], "y": self.rkm.pose[1], "theta": self.rkm.pose[2]}

        odom_msg = Odometry()
        odom_msg.header.stamp = self.get_clock().now().to_msg()
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_link'
        odom_msg.pose.pose.position.x = pose["x"]
        odom_msg.pose.pose.position.y = pose["y"]
        odom_msg.pose.pose.position.z = 0.0
        quaternion = tf_transformations.quaternion_from_euler(0, 0, pose["theta"])
        odom_msg.pose.pose.orientation.x = quaternion[0]
        odom_msg.pose.pose.orientation.y = quaternion[1]
        odom_msg.pose.pose.orientation.z = quaternion[2]
        odom_msg.pose.pose.orientation.w = quaternion[3]
        odom_msg.twist.twist.linear.x = self.rkm.speed[0]  ## Linear speed of the robot
        odom_msg.twist.twist.angular.z = self.rkm.speed[1]  ## Angular speed of the robot
        
        transform_stamped = TransformStamped()
        transform_stamped.header.stamp = self.get_clock().now().to_msg()
        transform_stamped.header.frame_id = 'world'
        transform_stamped.child_frame_id = 'base_link'
        transform_stamped.transform.translation.x = pose["x"]
        transform_stamped.transform.translation.y = pose["y"]
        transform_stamped.transform.translation.z = 0.0
        quaternion = tf_transformations.quaternion_from_euler(0, 0, pose["theta"])
        transform_stamped.transform.rotation.x = quaternion[0]
        transform_stamped.transform.rotation.y = quaternion[1]
        transform_stamped.transform.rotation.z = quaternion[2]
        transform_stamped.transform.rotation.w = quaternion[3]
        
        self.odom_publisher.publish(odom_msg)
        self.tf_broadcaster.sendTransform(transform_stamped)    


def main():
    """!
    Main function to initialize and run the Encoder node.
    """
    myRKM = KinematicModel()
    rclpy.init(args=None)
    encoder = Encoder(robot_kinematic_model=myRKM)
    encoder.speed_command_pile = [[0, 0]]
    rclpy.spin(encoder)
    rclpy.shutdown()

if __name__ == "__main__":
    main()