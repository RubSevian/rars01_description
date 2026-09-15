# Go2 + RARS01 geometry (`go2_arm` branch)

This branch is the geometry workspace for mounting the RARS01 manipulator on Unitree Go2. It deliberately does **not** change the RL controller in `workshop_legged_gym`.

## Source of truth

- RARS01 canonical model: `urdf/rars01.urdf`.
- Go2: pinned git submodule `external/workshop_legged_gym`.
- Mount transform: `config/go2_arm_mount.json`.

Do not add Isaac-specific corrections to `rars01.urdf`. ROS2/RViz/IK must always use canonical geometry.

## Generated variants

Run:

```bash
git checkout go2_arm
git submodule update --init --recursive
python3 tools/build_go2_arm_geometry.py
```

The generator creates four files:

```text
urdf/go2_arm_dynamic_base.urdf
urdf/go2_arm_static_base.urdf
urdf/go2_arm_dynamic_train.urdf
urdf/go2_arm_static_train.urdf
```

### Base variants

```text
go2_arm_dynamic_base.urdf
```

ROS2/RViz geometry with movable RARS01 joints.

```text
go2_arm_static_base.urdf
```

Same canonical geometry with RARS01/gripper joints fixed at q=0.

Both base files keep the canonical RARS01 visual and collision STL geometry.

### Train variants

```text
go2_arm_dynamic_train.urdf
go2_arm_static_train.urdf
```

These are Isaac-training derivatives. They preserve:

- the same mount transform;
- link/joint kinematics;
- mass;
- COM;
- inertia;
- **all RARS01 visual STL meshes by default**.

For the first large-parallel locomotion runs only the detailed RARS01 `<collision>` STL elements are removed. The visual STL files must remain present so the robot can still be inspected in Isaac Gym.

If RARS01 train visuals ever disappear unexpectedly, the generator now fails because it checks that the base/train RARS01 visual counts match.

For a deliberate no-arm-visual diagnostic only:

```bash
python3 tools/build_go2_arm_geometry.py --strip-train-arm-visuals
```

Do not use that flag for the normal train asset.

## Isaac visual orientation note

The current Go2 configuration uses:

```python
flip_visual_attachments = True
```

Isaac Gym applies this globally to the complete asset. The stock Go2 DAE meshes and RARS01 SolidWorks STL meshes may therefore render with different orientation conventions. This is a **train-backend visual issue** and must not be fixed by modifying the canonical RARS01 ROS2 model.

The train STL meshes are intentionally retained while we determine/implement the correct Isaac-specific visual conversion. Physics (`joint origin`, mass, COM and inertia) must remain canonical.

## Mount frame

Tune only:

```text
config/go2_arm_mount.json
```

Current starting value:

```json
{
  "parent_link": "base",
  "child_link": "base_link",
  "xyz_m": [0.0, 0.0, 0.060],
  "rpy_rad": [0.0, 0.0, 0.0]
}
```

The `z = 0.060 m` value is only a fitting starting point. The final X/Y/Z/yaw should be matched to the real mounting plate/base when its geometry is added.

## RViz fitting

The launch file always uses the canonical dynamic base variant:

```bash
colcon build --symlink-install --packages-select rars01_description
source install/setup.bash
ros2 launch rars01_description display_go2_arm.launch.py
```

`display_go2_arm.launch.py` loads:

```text
go2_arm_dynamic_base.urdf
```

so Isaac-specific train handling cannot silently alter the ROS2 visualization.

## Static Stage 0 invariant

Both static variants must expose exactly the 12 movable Go2 leg joints. The generator validates this and fails if the source models change and invalidate that assumption.
