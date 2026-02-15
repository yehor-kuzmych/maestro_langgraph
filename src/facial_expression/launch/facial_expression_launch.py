from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='facial_expression',
            executable='facial_expression_server',
            name='facial_expression_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'image_folder': '/home/plantroid/rooted/src/facial_expression/facial_expression/IMG/'}
            ]
        )
    ])
