from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_memory',
            executable='memory_server',
            name='memory_server_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'db_folder_path': '/home/plantroid/rooted/src/robot_memory/db/'}
            ]
        )
    ])