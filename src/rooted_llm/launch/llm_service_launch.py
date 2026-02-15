from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rooted_llm',
            executable='llm',
            name='llm_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'mode': 'local',
                 'IP': '127.0.0.1',
                 'PORT': '5050',}
            ]
        )
    ])
