# Go2 + RARS01 geometry (`go2_arm` branch)

This branch is the geometry workspace for mounting the RARS01 manipulator on Unitree Go2.
It deliberately does **not** change the RL controller in `workshop_legged_gym`.

## Sources

- RARS01: `urdf/rars01.urdf` from this repository.
- Go2: pinned git submodule `external/workshop_legged_gym` at the current `walk_diplom` source revision.
- Go2 visual meshes are installed from the submodule as `package://rars01_description/go2_dae/...`.

## Mount frame

The only mount transform to tune is:

`config/go2_arm_mount.json`

Initial value:

```json
{
  "xyz_m": [0.0, 0.0, 0.060],
  "rpy_rad": [0.0, 0.0, 0.0]
}
```

Conventions:

- parent: Go2 `base`;
- child: RARS01 `base_link`;
- Go2 +X is forward (front hip origins are at x = +0.1934 m, rear at x = -0.1934 m);
- with RARS01 joints at zero and mount yaw = 0, the `End_link` origin is approximately
  `[+0.3013, +0.00015, +0.1974] m` relative to the manipulator base, so the arm points generally toward Go2 +X.

The initial `z = 0.060 m` is only a fitting starting point. The Go2 base collision is 0.114 m high, so its nominal top is about +0.057 m from the `base` origin. The final X/Y/Z/yaw must be matched to the real four-screw mounting plate.

## Build the combined URDFs

Clone/update the branch together with the submodule:

```bash
git checkout go2_arm
git submodule update --init --recursive
python3 tools/build_go2_arm_geometry.py
```

The builder creates:

```text
urdf/go2_arm_dynamic.urdf
urdf/go2_arm_static.urdf
urdf/go2_arm_static_train.urdf
```

### `go2_arm_dynamic.urdf`

For geometry fitting in RViz. Go2 and the RARS01 are one URDF tree, while the arm joints remain movable. Use the joint-state GUI to inspect different arm poses without changing the mount transform.

### `go2_arm_static.urdf`

RARS01 and gripper joints are converted to fixed joints at q = 0. The only movable joints left are the 12 Go2 leg joints. This is the geometry variant intended for the first fixed-arm locomotion baseline.

### `go2_arm_static_train.urdf`

Same q = 0 fixed-arm model, but collision elements are removed from RARS01 links. This keeps the arm mass/inertia in the articulation while avoiding expensive detailed STL contacts during the first large parallel training run. We can replace these later with simple primitive collisions.

## Expected mass check

From the current URDF inertials:

- Go2 URDF mass sum: about **15.019 kg**;
- RARS01 URDF mass sum including gripper links: about **4.132 kg**;
- combined URDF mass sum: about **19.151 kg**.

These are URDF inertial sums, not a claim about measured real-robot mass. The builder prints the parsed values again each time it runs.

## RViz fitting

After generating the URDFs:

```bash
colcon build --symlink-install --packages-select rars01_description
source install/setup.bash
ros2 launch rars01_description display_go2_arm.launch.py
```

Then in RViz add a `RobotModel` display if it is not already present. Use `joint_state_publisher_gui` to move the arm and inspect clearances.

For a mount adjustment, edit only:

```text
config/go2_arm_mount.json
```

then rerun:

```bash
python3 tools/build_go2_arm_geometry.py
```

## Before using it in RL

Do not modify the current `go2_walk` controller yet. The dynamic combined model has more than 12 movable joints; the current Legged-Gym controller assumes the controlled DOF vector matches its action/control tensors. For the first baseline use the generated **static** geometry, then separately implement `leg_dof_indices` / `arm_dof_indices` when we move to the independently controlled arm stage.
