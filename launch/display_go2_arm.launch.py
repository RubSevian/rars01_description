from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Dynamic geometry is intentionally used here: joint_state_publisher_gui
    # can move the RARS01 joints while the mount transform stays fixed.
    urdf = PathJoinSubstitution(
        [FindPackageShare("rars01_description"), "urdf", "go2_arm_dynamic.urdf"]
    )
    robot_description = ParameterValue(Command(["cat ", urdf]), value_type=str)

    return LaunchDescription(
        [
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
            ),
            Node(package="rviz2", executable="rviz2", output="screen"),
        ]
    )
