import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    tb3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    world = os.path.join(tb3_gazebo, 'worlds', 'turtlebot3_world.world')
    urdf = os.path.join(tb3_gazebo, 'urdf', 'turtlebot3_burger.urdf')
    bridge_cfg = os.path.join(tb3_gazebo, 'params', 'turtlebot3_burger_bridge.yaml')

    with open(urdf, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([
        # Server only — no GUI
        ExecuteProcess(
            cmd=['gz', 'sim', '-s', '-r', world, '--force-version', '10', '-v2'],
            output='screen'
        ),

        # Wait then spawn robot
        TimerAction(period=3.0, actions=[
            ExecuteProcess(
                cmd=['ros2', 'run', 'ros_gz_sim', 'create',
                     '-name', 'turtlebot3_burger',
                     '-file', urdf],
                output='screen'
            ),
        ]),

        # ROS<->Gazebo bridge
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'config_file': bridge_cfg}],
            output='screen'
        ),

        # Robot state publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': True
            }],
            output='screen'
        ),
    ])
