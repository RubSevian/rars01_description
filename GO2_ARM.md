# Go2 + RARS01 geometry (`go2_arm` branch)

This branch is the geometry workspace for mounting the RARS01 manipulator on Unitree Go2.
It deliberately does **not** change the RL controller in `workshop_legged_gym`.

## Sources

- RARS01 source of truth: `urdf/rars01.urdf` from this repository.
- Go2: pinned git submodule `external/workshop_legged_gym` at the current `walk_diplom` source revision.
- Go2 visual meshes are installed from the submodule as `package://rars01_description/go2_dae/...`.

The canonical RARS01 URDF must stay backend-independent. ROS2/RViz/IK must never depend on Isaac-specific mesh corrections.

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
- Go2 +X is forward;
- with RARS01 joints at zero and mount yaw = 0, the arm points generally toward Go2 +X.

The initial `z = 0.060 m` is only a fitting starting point. The final X/Y/Z/yaw must be matched to the real mounting plate/base.

## Build all combined URDFs

```bash
git checkout go2_arm
git submodule update --init --recursive
python3 tools/build_go2_arm_geometry.py
```

The builder now creates four explicit backend/state combinations:

```text
urdf/go2_arm_dynamic_base.urdf
urdf/go2_arm_static_base.urdf
urdf/go2_arm_dynamic_train.urdf
urdf/go2_arm_static_train.urdf
```

Old generated names `go2_arm_dynamic.urdf` and `go2_arm_static.urdf` are removed by the builder to avoid ambiguity.

## Base variants — canonical ROS2/RViz geometry

### `go2_arm_dynamic_base.urdf`

Canonical combined Go2 + RARS01 model for ROS2/RViz and geometry fitting.

- RARS01 joints remain movable.
- Canonical RARS01 visuals are preserved.
- Canonical RARS01 collisions are preserved.
- Mass, COM, inertia and joint frames are unchanged.

`display_go2_arm.launch.py` always loads this file.

### `go2_arm_static_base.urdf`

Same canonical geometry, but all RARS01/gripper movable joints are converted to fixed joints at `q = 0`.

Only the 12 Go2 leg joints remain movable.

This file is useful for ROS2/static geometry checks and for comparing the exact fixed pose with the train variant.

## Train variants — Isaac-specific derived assets

Isaac Gym has one global `flip_visual_attachments` switch per loaded asset. The stock Go2 DAE meshes and RARS01 SolidWorks STL meshes do not share the same visual convention, so one global flip setting cannot be assumed to render both correctly.

Therefore training URDFs are treated as **derived backend files**, not as the geometry source of truth.

### `go2_arm_dynamic_train.urdf`

- RARS01 joints remain movable.
- RARS01 mass/COM/inertia and kinematics remain present.
- detailed RARS01 collision meshes are removed;
- RARS01 visual meshes are removed by default to avoid showing a misleading flipped arm under Go2's `flip_visual_attachments=True`.

This is intended for the later independently controlled moving-arm training stage.

### `go2_arm_static_train.urdf`

- RARS01/gripper joints are fixed at `q = 0`;
- only the 12 Go2 leg joints remain movable;
- RARS01 mass/COM/inertia remain physically present;
- detailed RARS01 collisions are removed;
- RARS01 visuals are removed by default for the same Isaac visual-convention reason.

This is the intended Stage 0 locomotion baseline asset.

## Optional Isaac visual debug

If you explicitly want to see the raw RARS01 STL visuals inside the train URDFs while diagnosing the importer:

```bash
python3 tools/build_go2_arm_geometry.py --keep-train-arm-visuals
```

This affects only generated train visuals, never physics. With the current Go2 `flip_visual_attachments=True`, those STL visuals may appear flipped/misoriented. Do not "fix" that by changing the canonical `rars01.urdf`.

Later, if full Isaac visualization is required, create train-specific converted mesh copies. That conversion belongs only to the `*_train` pipeline.

## Invariant between base and train

For a given dynamic/static state, base and train variants must have identical kinematics and DOF structure:

```text
dynamic_base DOFs == dynamic_train DOFs
static_base DOFs  == static_train DOFs
```

The builder checks this automatically.

Both static variants must contain exactly the original 12 movable Go2 leg joints. The builder fails loudly otherwise.

## Expected mass check

From the current URDF inertials:

- Go2 URDF mass sum: about **15.019 kg**;
- RARS01 URDF mass sum including gripper links: about **4.132 kg**;
- combined URDF mass sum: about **19.151 kg**.

These are URDF inertial sums, not measured real-robot masses.

## RViz fitting

After generating the URDFs:

```bash
colcon build --symlink-install --packages-select rars01_description
source install/setup.bash
ros2 launch rars01_description display_go2_arm.launch.py
```

The launch file loads only:

```text
go2_arm_dynamic_base.urdf
```

Use `joint_state_publisher_gui` to move the manipulator and inspect clearances.

For a mount adjustment, edit only:

```text
config/go2_arm_mount.json
```

then rerun:

```bash
python3 tools/build_go2_arm_geometry.py
```

## When the real mounting base is added

Add the real mounting-base geometry to the canonical model/tree, for example:

```text
Go2 base
  -> fixed mount
  -> mounting_base
  -> RARS01 base_link
```

Then regenerate all four variants. Do not add the physical mounting base only to an Isaac train file, otherwise ROS2 and simulation geometry will diverge.

## RL stages

Stage 0:

```text
go2_arm_static_train.urdf
Go2 legs: 12-DOF RL
RARS01: fixed q=0 physical payload
```

Later moving-arm stage:

```text
go2_arm_dynamic_train.urdf
Go2 legs: RL
RARS01: independently controlled arm
```

At that later stage the controller must explicitly separate `leg_dof_indices` and `arm_dof_indices`; do not expand the locomotion policy to 18 actions by accident.
