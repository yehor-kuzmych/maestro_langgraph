from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='other_sensors',
            executable='fake_sensor_server',
            name='sensor_server_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {}
            ]
        )
    ])