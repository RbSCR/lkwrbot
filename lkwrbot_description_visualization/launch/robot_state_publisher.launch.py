"""
Launchfile for robot-state-publisher of the LKWrbot robot.

Usage:
- Build packages (this and lkwrbot_description) with colcon
- Launch the robot_state_publisher and the joint_state_publisher_gui
  with "ros2 launch lkwrbot_description_visualization robot_state_publisher.launch.py"

- Launch RVIZ with rviz2
  In rviz2
  - Set your fixed frame to world
  - Add a RobotModel display, with the topic set to /robot_description, and alpha set to 0.8
  - Add a TF display with names enabled.

"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    # Specify the name of the package and path to xacro file within the package
    pkg_name = 'lkwrbot_description'
    urdf_subpath = 'urdf'
    urdf_filename = 'base.urdf.xacro'

    # Use xacro to process the file
    xacro_file = os.path.join(get_package_share_directory(pkg_name), urdf_subpath, urdf_filename)
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    #  Configure the node's
    node_robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_raw}]
        # add other parameters here if required
    )

    node_joint_state_publisher_gui_cmd = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen'
    )

    ld = LaunchDescription()

    ld.add_action(node_joint_state_publisher_gui_cmd)
    ld.add_action(node_robot_state_publisher_cmd)

    return ld
