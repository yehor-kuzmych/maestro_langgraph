from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rooted_encoder',
            executable='encoder_virtual',
            name='virtual_encoder_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'DEVICENAME': '/dev/ttyServo',
                 'BAUDRATE':'1_000_000'}
            ]
        ),
        Node(
            package='rooted_encoder',
            executable='controller_virtual',
            name='virtual_controller_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'DEVICENAME': '/dev/ttyServo',
                 'BAUDRATE':'1_000_000'}
            ]
        )
    ])