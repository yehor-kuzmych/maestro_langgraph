from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='other_sensors',
            executable='sensor_server',
            name='sensor_server_node',
            output='screen',
            emulate_tty=sTrue,
            parameters=[
                {'soil_sensor_path': '/dev/ttyNPK',
                 'arduino_path': '/dev/ttyArduino',
                 'sonar_path': '/dev/ttySonar',}
            ]
        )
    ])