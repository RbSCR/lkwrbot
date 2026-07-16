#!/usr/bin/env python3
"""
Launch the LKWrbot robot control stack.

"""

import yaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
from launch.actions import TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch.substitutions import FindExecutable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.actions import SetRemap
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def launch_setup(context):
    serial_port = LaunchConfiguration('sts_serial_port').perform(context)
    use_mock = LaunchConfiguration('use_mock').perform(context)
    diagnostics = LaunchConfiguration('diagnostics').perform(context)
    launch_joy = LaunchConfiguration('joy').perform(context).lower() in ('true', '1')
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context).lower() in ('true', '1')

    pkg_desc = FindPackageShare('lkwrbot_description').perform(context)
    pkg_ctrl = FindPackageShare('lkwrbot_control').perform(context)
    xacro = FindExecutable(name='xacro').perform(context)

    urdf = f'{pkg_desc}/urdf/base.urdf.xacro'

    _cfg = yaml.safe_load(open(f'{pkg_ctrl}/config/base/lkwrbot_urdf_config.yaml'))

    final_serial_port = serial_port if serial_port else _cfg['serial_port']
    final_use_mock = use_mock if use_mock else str(_cfg['use_mock']).lower()

    xacro_cmd = (
        f'{xacro} {urdf}'
        f' serial_port:={final_serial_port}'
        f' use_mock:={final_use_mock}'
        f' baud_rate:={_cfg["baud_rate"]}'
        f' use_sync_write:={str(_cfg["use_sync_write"]).lower()}'
        f' left_motor_id:={_cfg["left_motor_id"]}'
        f' back_motor_id:={_cfg["back_motor_id"]}'
        f' right_motor_id:={_cfg["right_motor_id"]}'
        f' sts_max_velocity_steps:={_cfg["sts_max_velocity_steps"]}'
        f' proportional_acc_max:={_cfg["proportional_acc_max"]}'
    )

    robot_description = {
        'robot_description': ParameterValue(Command([xacro_cmd]), value_type=str)
    }

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='log',
        parameters=[robot_description, {'use_sim_time': use_sim_time}],
        name='robot_state_publisher',
        emulate_tty=True,
        arguments=['--ros-args', '--log-level', 'WARN'],
    )

    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            robot_description,
            f'{pkg_ctrl}/config/base/lkwrbot_controllers.yaml',
            {'use_sim_time': use_sim_time},
        ],
        remappings=[('/diagnostics', '/controller_manager/diagnostics')],
        output='log',
        emulate_tty=True,
        arguments=['--ros-args', '--log-level', 'rclcpp:=ERROR'],
    )

    teleop_node = Node(
        package='joy_teleop',
        executable='joy_teleop',
        name='joy_teleop',
        parameters=[
            f'{pkg_ctrl}/config/base/lkwrbot_teleop.yaml',
            {'use_sim_time': use_sim_time},
        ],
        output='screen',
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='log',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    joint_state_broadcaster_spawner = TimerAction(
        period=2.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster', '-c', '/controller_manager'],
            output='both',
        )],
    )

    extra_spawner_nodes = [
        Node(package='controller_manager', executable='spawner',
             arguments=['base_controller', '-c', '/controller_manager'], output='both'),
        Node(package='controller_manager', executable='spawner',
             arguments=['imu_sensor_broadcaster', '-c', '/controller_manager'], output='both'),
    ]

    extra_spawners = TimerAction(period=2.5, actions=extra_spawner_nodes)

    motor_diagnostics = GroupAction([
        SetRemap('/diagnostics', '/base/diagnostics'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([FindPackageShare('sts_hardware_interface'),
                                      'launch', 'motor_diagnostics.launch.py'])
            ])
        ),
    ])

    actions = [
        robot_state_publisher,
        controller_manager,
        joint_state_broadcaster_spawner,
        extra_spawners,
        teleop_node,
    ]

    if launch_joy:
        actions.append(joy_node)

    if diagnostics.lower() == 'true':
        actions.append(TimerAction(period=3.0, actions=[motor_diagnostics]))
        actions.append(TimerAction(
            period=3.0,
            actions=[Node(
                package='bno055_hardware_interface',
                executable='bno055_diagnostics',
                name='bno055_diagnostics',
                output='log',
                parameters=[
                    f'{pkg_ctrl}/config/base/lkwrbot_bno055_diagnostics.yaml',
                    {'enable_mock_mode': final_use_mock},
                ],
                remappings=[('/diagnostics', '/imu/diagnostics')],
            )],
        ))

    return actions


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            'sts_serial_port',
            default_value='',
            description='Serial port override; '
                        'empty string means use lkwrbot_urdf_config.yaml value',
        ),
        DeclareLaunchArgument(
            'use_mock',
            default_value='',
            description='Mock mode override (true/false); '
                        'empty string means use lkwrbot_urdf_config.yaml value',
        ),
        DeclareLaunchArgument(
            'diagnostics',
            default_value='true',
            description='Launch motor and IMU diagnostics nodes',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use /clock from a simulator instead of system time.',
        ),
        DeclareLaunchArgument(
            'joy',
            default_value='false',
            description='Launch joy_node on this device.'
                        'Set true when the joystick is connected locally; '
                        'leave false when /joy is published from a remote device.',
        ),
    ]

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
