# rars01_description

Структура рабочих файлов и исходного SolidWorks-экспорта описана в
[`ARCHITECTURE.md`](ARCHITECTURE.md).

Пакет описания робота RARS01 для ROS 2.

## Содержимое

- `urdf/rars01.urdf` — полная модель: `arm_mount_link → base_link → RARS01`;
- `urdf/rars01_control.urdf` — модель руки от `base_link` для IK и hand-eye;
- `meshes/` — visual и collision STL актуальной модели;
- `launch/display.launch.py` — просмотр модели и ручная проверка суставов;
- `source/solidworks_export/` — исходный экспорт SolidWorks без ROS-правок.

## Сборка

```bash
source /opt/ros/humble/setup.bash
colcon build \
  --symlink-install \
  --event-handlers console_direct+ \
  --cmake-args \
  -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

ROS 2 Humble должен собираться системным Python 3.10. Если CMake раньше
закэшировал Miniconda Python, удалите `build/` или добавьте
`--cmake-clean-cache`.

## Просмотр модели

```bash
ros2 launch rars01_description display.launch.py
```

`arm_mount_link` — корень полной сборки и система крепления к Go2;
`base_link` — база самого манипулятора. Имена суставов руки: `joint1..joint6`.
Захват состоит из двух призматических звеньев:
`gripper_left_joint` и `gripper_right_joint`. ROS-совместимые изменения вносятся
согласованно в полную и control-модель; исходный SolidWorks export сохраняется
отдельно без ROS-правок.
