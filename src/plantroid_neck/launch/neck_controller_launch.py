# example.launch.yaml
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='plantroid_neck',
            executable='neck_server',
            name='neck_server_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'raspi': 'True'}
            ]
        )
    ])