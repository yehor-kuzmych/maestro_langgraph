from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='listening_module',
            executable='listener_server',
            name='listener_server_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'audio_folder_path': '/home/plantroid/rooted/src/robot_memory/db/audio'}
            ]
        )
    ])
