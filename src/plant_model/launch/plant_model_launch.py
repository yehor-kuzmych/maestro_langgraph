from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='plant_model',
            executable='plant_monitor',
            name='plant_monitoring_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'plant_info_file':'/home/plantroid/rooted/src/plant_model/plant_characteristics.json',
                 'db_path':'/home/plantroid/rooted/src/robot_memory/db/plant.db'
                 }
            ]
        )
    ])
