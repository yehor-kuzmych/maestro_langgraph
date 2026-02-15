from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rooted_encoder',
            executable='encoder',
            name='encoder_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'DEVICENAME': '/dev/ttyServo',
                 'BAUDRATE':'1_000_000'}
            ]
        )
    ])
