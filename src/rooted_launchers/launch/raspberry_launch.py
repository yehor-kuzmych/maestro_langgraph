from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Define parameters to override or remap for the included launch files
    home_dir = '/home/plantroid'
    param_override_pkg1 =  {} #  you can delete these if needed, but it is good in case you add more parameters to this module
    param_override_pkg2 =  {'mode':'local',
                            'IP':'127.0.0.1',
                            'PORT':'5050'}
    param_override_pkg3 =  {'DEVICENAME': '/dev/ttyServo',
                            'BAUDRATE':'1_000_000'}
    param_override_pkg4 =  {'raspi': 'True'}
    param_override_pkg5 =  {} #  you can delete these if needed, but it is good in case you add more parameters to this module
    param_override_pkg6 =  {} #  you can delete these if needed, but it is good in case you add more parameters to this module
    param_override_pkg7 =  {'audio_folder_path': f'{home_dir}/rooted/src/robot_memory/db/audio'}
    param_override_pkg8 =  {'image_folder':f'{home_dir}/rooted/src/facial_expression/facial_expression/IMG/'}
    param_override_pkg9 =  {'mode': 'local',
                            'model': 'espeak-ng',
                            'IP': '127.0.0.1',
                            'PORT': '5049'}
    param_override_pkg10 = {'db_folder_path': f'{home_dir}/rooted/src/robot_memory/db/'}
    param_override_pkg11 = {} #  you can delete these if needed, but it is good in case you add more parameters to this module
    param_override_pkg12 = {'plant_info_file':f'{home_dir}/rooted/src/plant_model/plant_characteristics.json',
                            'db_path':f'{home_dir}/rooted/src/robot_memory/db/plant.db'}
    param_override_pkg13 = {'identity_db': f'{home_dir}/rooted/src/robot_memory/db/people.db'}
    param_override_pkg14 = {'dialog_json': f'{home_dir}/rooted/src/maestro/maestro/dialogue.json',
                            'store_chat_log':'True', 
                            'keep_eye_contact':'True', 
                            'pc_mode':'False', 
                            'store_emotion_change':'True', 
                            'robot_name':'plant droid'}

    # Include launch files from other packages
    pkg1_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('rooted_busy'), '/launch/busy_launch.py']
        )
    )

    pkg2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('rooted_llm'), '/launch/llm_service_launch.py']),
        launch_arguments={'mode':param_override_pkg2.get('mode'),
                          'IP':param_override_pkg2.get('IP'),
                          'PORT':param_override_pkg2.get('PORT')}.items())

    pkg3_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('rooted_encoder'), '/launch/encoder_launch.py']),
        launch_arguments={'DEVICENAME': param_override_pkg3.get('DEVICENAME'), 
                          'BAUDRATE': param_override_pkg3.get('BAUDRATE')}.items())

    pkg4_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('plantroid_neck'), '/launch/neck_controller_launch.py']
        ),
        launch_arguments={'raspi':param_override_pkg4.get('raspi')}.items()
    )

    pkg5_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('rooted_gestures'), '/launch/gestures_service_launch.py']))

    pkg6_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('movement_module'), '/launch/movement_module_launch.py']
        )
    )

    pkg7_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('listening_module'), '/launch/listener_launch.py']
        ),
        launch_arguments={'audio_folder_path':param_override_pkg7.get('audio_folder_path')}.items()
    )

    pkg8_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('facial_expression'), '/launch/facial_expression_launch.py']
        ),
        launch_arguments={'image_folder': param_override_pkg8.get('image_folder')}.items()
    )

    pkg9_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('rooted_speech_synthesizer'), '/launch/tts_service_launch.py']
        ),
        launch_arguments={'mode':param_override_pkg9.get('mode'),
                          'model':param_override_pkg9.get('model'),
                          'IP':param_override_pkg9.get('IP'),
                          'PORT':param_override_pkg9.get('PORT')}.items()
    )

    pkg10_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('robot_memory'), '/launch/robot_memory_launch.py']
        ),
        launch_arguments={'db_folder_path':param_override_pkg10.get('db_folder_path')}.items()
    )

    pkg11_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('other_sensors'), '/launch/sensors_launch.py']))

    pkg12_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('plant_model'), '/launch/plant_model_launch.py']
        ),
        launch_arguments={'plant_info_file':param_override_pkg12.get('plant_info_file'),
                          'db_path':param_override_pkg12.get('db_path')}.items()
    )

    pkg13_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('vision_module'), '/launch/vision_module_launch.py']
        ),
        launch_arguments={'identity_db':param_override_pkg13.get('identity_db')}.items()
    )

    pkg14_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('maestro'), '/launch/maestro_launch.py']
        ),
        launch_arguments={'dialog_json':param_override_pkg14.get('dialog_json'),
                          'store_chat_log':param_override_pkg14.get('store_chat_log'),
                          'keep_eye_contact':param_override_pkg14.get('keep_eye_contact'),
                          'pc_mode':param_override_pkg14.get('pc_mode'),
                          'store_emotion_change':param_override_pkg14.get('store_emotion_change'),
                          'robot_name':param_override_pkg14.get('robot_name'),}.items()
    )

    # Return the combined launch description
    return LaunchDescription([pkg1_launch,
                              pkg2_launch,
                              pkg3_launch,
                              pkg4_launch,
                              pkg5_launch,
                              pkg6_launch,
                              pkg7_launch,
                              pkg8_launch,
                              pkg9_launch,
                              pkg10_launch,
                              pkg11_launch,
                              pkg12_launch,
                              pkg13_launch,
                              pkg14_launch])
