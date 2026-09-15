#!/usr/bin/env python3
"""Build canonical ROS2 and Isaac-training Go2 + RARS01 URDF variants.

Outputs:
  urdf/go2_arm_dynamic_base.urdf   - ROS2/RViz: movable RARS01, canonical visuals
  urdf/go2_arm_static_base.urdf    - ROS2/RViz: RARS01 fixed at q=0, canonical visuals
  urdf/go2_arm_dynamic_train.urdf  - Isaac: movable RARS01, train variant
  urdf/go2_arm_static_train.urdf   - Isaac: RARS01 fixed at q=0, train variant

Why base/train are separate:
Isaac Gym's global ``flip_visual_attachments`` option is applied to the whole
combined asset. The stock Go2 DAE meshes and the RARS01 SolidWorks STL meshes
may not share the same visual convention, so ROS2/RViz and Isaac-specific
handling must stay separated.

The *_base files are the canonical ROS2/RViz/IK geometry and preserve all
RARS01 visuals/collisions. The *_train files preserve the same kinematics,
mass, COM and inertia and, by default, also preserve all RARS01 visual STL
meshes. Only the detailed RARS01 collision meshes are removed for the first
large-parallel locomotion runs. If needed for diagnosis, RARS01 train visuals
can be explicitly stripped with ``--strip-train-arm-visuals``.

The Go2 source is pinned as a git submodule under external/workshop_legged_gym.
Only Python standard library is required.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GO2 = ROOT / "external/workshop_legged_gym/resources/robots/go2/urdf/go2.urdf"
DEFAULT_ARM = ROOT / "urdf/rars01.urdf"
DEFAULT_MOUNT = ROOT / "config/go2_arm_mount.json"

GO2_MESH_PREFIX = "package://rars01_description/go2_dae/"
ARM_MESH_PREFIX = "package://rars01_description/meshes/"

LEGACY_OUTPUTS = (
    ROOT / "urdf/go2_arm_dynamic.urdf",
    ROOT / "urdf/go2_arm_static.urdf",
)


class GeometryError(RuntimeError):
    pass


def _load_robot(path: Path) -> ET.Element:
    if not path.exists():
        raise GeometryError(f"URDF not found: {path}")
    root = ET.parse(path).getroot()
    if root.tag != "robot":
        raise GeometryError(f"Expected <robot> root in {path}, got <{root.tag}>")
    return root


def _load_mount(path: Path) -> dict:
    if not path.exists():
        raise GeometryError(f"Mount config not found: {path}")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for key in ("parent_link", "child_link", "xyz_m", "rpy_rad"):
        if key not in cfg:
            raise GeometryError(f"Missing '{key}' in {path}")
    if len(cfg["xyz_m"]) != 3 or len(cfg["rpy_rad"]) != 3:
        raise GeometryError("xyz_m and rpy_rad must contain exactly 3 values")
    return cfg


def _names(root: ET.Element, tag: str) -> set[str]:
    return {x.attrib["name"] for x in root.findall(tag) if "name" in x.attrib}


def _validate_no_name_collisions(go2: ET.Element, arm: ET.Element) -> None:
    link_overlap = _names(go2, "link") & _names(arm, "link")
    joint_overlap = _names(go2, "joint") & _names(arm, "joint")
    if link_overlap:
        raise GeometryError(f"Duplicate link names: {sorted(link_overlap)}")
    if joint_overlap:
        raise GeometryError(f"Duplicate joint names: {sorted(joint_overlap)}")


def _rewrite_go2_meshes(root: ET.Element) -> None:
    for mesh in root.iter("mesh"):
        filename = mesh.get("filename")
        if not filename:
            continue
        mesh.set("filename", GO2_MESH_PREFIX + Path(filename).name)


def _rewrite_arm_meshes(root: ET.Element) -> None:
    for mesh in root.iter("mesh"):
        filename = mesh.get("filename")
        if not filename:
            continue
        if "/meshes/" in filename:
            mesh_name = filename.split("/meshes/", 1)[1]
        else:
            mesh_name = Path(filename).name
        mesh.set("filename", ARM_MESH_PREFIX + mesh_name)


def _mount_joint(cfg: dict) -> ET.Element:
    joint = ET.Element("joint", {"name": "go2_to_rars01_mount", "type": "fixed"})
    ET.SubElement(
        joint,
        "origin",
        {
            "xyz": " ".join(f"{float(v):.9g}" for v in cfg["xyz_m"]),
            "rpy": " ".join(f"{float(v):.9g}" for v in cfg["rpy_rad"]),
        },
    )
    ET.SubElement(joint, "parent", {"link": cfg["parent_link"]})
    ET.SubElement(joint, "child", {"link": cfg["child_link"]})
    return joint


def _merge(
    go2_source: ET.Element,
    arm_source: ET.Element,
    mount_cfg: dict,
) -> tuple[ET.Element, set[str], set[str]]:
    go2 = copy.deepcopy(go2_source)
    arm = copy.deepcopy(arm_source)
    _validate_no_name_collisions(go2, arm)
    _rewrite_go2_meshes(go2)
    _rewrite_arm_meshes(arm)

    if mount_cfg["parent_link"] not in _names(go2, "link"):
        raise GeometryError(f"Go2 parent link '{mount_cfg['parent_link']}' does not exist")
    if mount_cfg["child_link"] not in _names(arm, "link"):
        raise GeometryError(f"RARS01 child link '{mount_cfg['child_link']}' does not exist")

    arm_link_names = _names(arm, "link")
    arm_joint_names = _names(arm, "joint")
    go2.set("name", "go2_rars01")

    for element in list(arm):
        go2.append(copy.deepcopy(element))
    go2.append(_mount_joint(mount_cfg))
    return go2, arm_link_names, arm_joint_names


def _fix_arm_joints(root: ET.Element, arm_joint_names: set[str]) -> None:
    removable = {
        "axis",
        "limit",
        "dynamics",
        "mimic",
        "safety_controller",
        "calibration",
    }
    for joint in root.findall("joint"):
        if joint.get("name") not in arm_joint_names:
            continue
        if joint.get("type") == "fixed":
            continue
        joint.set("type", "fixed")
        for child in list(joint):
            if child.tag in removable:
                joint.remove(child)


def _strip_link_elements(root: ET.Element, link_names: set[str], tag: str) -> None:
    for link in root.findall("link"):
        if link.get("name") not in link_names:
            continue
        for element in list(link.findall(tag)):
            link.remove(element)


def _prepare_train_variant(
    root: ET.Element,
    arm_link_names: set[str],
    *,
    strip_arm_visuals: bool,
) -> None:
    # Detailed RARS01 STL collision meshes are intentionally excluded from the
    # first large-scale locomotion runs. Mass/COM/inertia remain untouched.
    _strip_link_elements(root, arm_link_names, "collision")

    # Visual STL meshes are preserved by default. Isaac Gym applies
    # flip_visual_attachments globally to the whole asset, so their displayed
    # orientation may still need a train-specific correction later. They must
    # not disappear silently from the generated train URDF.
    if strip_arm_visuals:
        _strip_link_elements(root, arm_link_names, "visual")


def _sum_mass(root: ET.Element, selected_links: set[str] | None = None) -> float:
    total = 0.0
    for link in root.findall("link"):
        if selected_links is not None and link.get("name") not in selected_links:
            continue
        mass = link.find("./inertial/mass")
        if mass is not None and mass.get("value") is not None:
            total += float(mass.get("value"))
    return total


def _movable_joint_names(root: ET.Element) -> list[str]:
    return [
        j.get("name", "")
        for j in root.findall("joint")
        if j.get("type") not in (None, "fixed")
    ]


def _count_arm_visuals(root: ET.Element, arm_link_names: set[str]) -> int:
    count = 0
    for link in root.findall("link"):
        if link.get("name") in arm_link_names:
            count += len(link.findall("visual"))
    return count


def _write(root: ET.Element, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def _remove_legacy_outputs() -> None:
    for path in LEGACY_OUTPUTS:
        if path.exists():
            path.unlink()


def build(
    go2_path: Path,
    arm_path: Path,
    mount_path: Path,
    *,
    strip_train_arm_visuals: bool = False,
) -> None:
    go2_source = _load_robot(go2_path)
    arm_source = _load_robot(arm_path)
    mount_cfg = _load_mount(mount_path)

    merged, arm_links, arm_joints = _merge(go2_source, arm_source, mount_cfg)

    dynamic_base = copy.deepcopy(merged)
    static_base = copy.deepcopy(merged)
    dynamic_train = copy.deepcopy(merged)
    static_train = copy.deepcopy(merged)

    _fix_arm_joints(static_base, arm_joints)
    _fix_arm_joints(static_train, arm_joints)

    _prepare_train_variant(
        dynamic_train,
        arm_links,
        strip_arm_visuals=strip_train_arm_visuals,
    )
    _prepare_train_variant(
        static_train,
        arm_links,
        strip_arm_visuals=strip_train_arm_visuals,
    )

    paths = {
        "dynamic_base": ROOT / "urdf/go2_arm_dynamic_base.urdf",
        "static_base": ROOT / "urdf/go2_arm_static_base.urdf",
        "dynamic_train": ROOT / "urdf/go2_arm_dynamic_train.urdf",
        "static_train": ROOT / "urdf/go2_arm_static_train.urdf",
    }

    _remove_legacy_outputs()
    _write(dynamic_base, paths["dynamic_base"])
    _write(static_base, paths["static_base"])
    _write(dynamic_train, paths["dynamic_train"])
    _write(static_train, paths["static_train"])

    arm_mass = _sum_mass(merged, arm_links)
    system_mass = _sum_mass(merged)
    xyz = mount_cfg["xyz_m"]
    rpy = mount_cfg["rpy_rad"]

    dynamic_names = _movable_joint_names(dynamic_base)
    static_names = _movable_joint_names(static_base)
    train_dynamic_names = _movable_joint_names(dynamic_train)
    train_static_names = _movable_joint_names(static_train)

    if dynamic_names != train_dynamic_names:
        raise GeometryError("Dynamic base/train DOF lists differ")
    if static_names != train_static_names:
        raise GeometryError("Static base/train DOF lists differ")

    if len(static_names) != 12:
        raise GeometryError(
            "Expected exactly 12 movable joints in static variants, got "
            f"{len(static_names)}: {static_names}"
        )

    base_visual_count = _count_arm_visuals(dynamic_base, arm_links)
    train_visual_count = _count_arm_visuals(dynamic_train, arm_links)
    if not strip_train_arm_visuals and train_visual_count != base_visual_count:
        raise GeometryError(
            "RARS01 visuals unexpectedly disappeared from train variant: "
            f"base={base_visual_count}, train={train_visual_count}"
        )

    print("Built Go2 + RARS01 geometry")
    print(f"  mount xyz [m]: {xyz}")
    print(f"  mount rpy [rad]: {rpy}")
    print(f"  arm URDF mass: {arm_mass:.3f} kg")
    print(f"  combined URDF mass: {system_mass:.3f} kg")
    print(f"  dynamic movable joints: {len(dynamic_names)}")
    print(f"  static movable joints:  {len(static_names)}")
    print(f"  RARS01 base visuals: {base_visual_count}")
    print(f"  RARS01 train visuals: {train_visual_count}")
    print(f"  train arm visuals stripped: {strip_train_arm_visuals}")
    for path in paths.values():
        print(f"  {path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--go2-urdf", type=Path, default=DEFAULT_GO2)
    parser.add_argument("--arm-urdf", type=Path, default=DEFAULT_ARM)
    parser.add_argument("--mount", type=Path, default=DEFAULT_MOUNT)
    parser.add_argument(
        "--strip-train-arm-visuals",
        action="store_true",
        help="Explicitly remove RARS01 <visual> elements from *_train URDFs.",
    )
    args = parser.parse_args()

    try:
        build(
            args.go2_urdf.resolve(),
            args.arm_urdf.resolve(),
            args.mount.resolve(),
            strip_train_arm_visuals=args.strip_train_arm_visuals,
        )
    except (GeometryError, ET.ParseError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
