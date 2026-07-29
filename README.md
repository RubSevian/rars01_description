# rars01_description

ROS 2 description package for the RARS01 six-axis manipulator and its
single-motor gripper.

## Contents

- `urdf/rars01.urdf` — working ROS 2 model used by RViz and MoveIt.
- `source/solidworks_export/` — original SolidWorks URDF, CSV and ROS 1
  exporter files kept for reference.
- `meshes/` — visual and collision STL meshes.
- `launch/display.launch.py` — standalone model and joint-axis inspection.

The ROS joint-to-motor mapping is:

| ROS joint | SDK motor |
|---|---:|
| `joint1` ... `joint6` | 0 ... 5 |
| `gripper` | 6 |

## Standalone build

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Display the model:

```bash
ros2 launch rars01_description display.launch.py
```

## MoveIt integration

Place this repository next to `reBotArmController_ROS2` and build both from
their parent directory:

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install \
  --base-paths rars01_description reBotArmController_ROS2/src
source install/setup.bash

ros2 launch rebotarm_moveit_config demo.launch.py model:=rars
```

The original SolidWorks export should remain unchanged. Make ROS-specific
joint-name, package-path and controller compatibility changes in
`urdf/rars01.urdf`.
