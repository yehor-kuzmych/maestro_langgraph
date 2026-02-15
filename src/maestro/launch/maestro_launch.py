from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='maestro',
            executable='maestro',
            name='plantroid',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'dialog_json': '/home/plantroid/rooted/src/maestro/maestro/dialogue.json',
                 'store_chat_log':False, 
                 'keep_eye_contact':True, 
                 'pc_mode':False, 
                 'store_emotion_change':True, 
                 'robot_name':'plant droid'
                 }
            ]
        )
    ])
