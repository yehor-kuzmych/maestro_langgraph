from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    backend_arg = DeclareLaunchArgument(
        'backend',
        default_value='ollama',
        description='LLM backend: "ollama" or "lmstudio"'
    )

    model_name_arg = DeclareLaunchArgument(
        'model_name',
        default_value='qwen2:0.5b',
        description='Model name (for Ollama; LM Studio uses currently loaded model)'
    )

    base_url_arg = DeclareLaunchArgument(
        'base_url',
        default_value='',
        description='LLM server URL (auto-detected if empty: Ollama=localhost:11434, LM Studio=localhost:1234)'
    )

    maestro_langgraph_node = Node(
        package='maestro_langgraph',
        executable='maestro_langgraph_node',
        name='maestro_langgraph',
        output='screen',
        parameters=[{
            'backend': LaunchConfiguration('backend'),
            'model_name': LaunchConfiguration('model_name'),
            'base_url': LaunchConfiguration('base_url'),
        }],
    )

    return LaunchDescription([
        backend_arg,
        model_name_arg,
        base_url_arg,
        maestro_langgraph_node,
    ])
