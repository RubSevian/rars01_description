# rars01_description

Структура рабочих файлов и исходного SolidWorks-экспорта описана в
[`ARCHITECTURE.md`](ARCHITECTURE.md).

Пакет описания робота RARS01 для ROS 2.

## Содержимое

- `urdf/rars01.urdf` — рабочая модель робота;
- `meshes/` — visual и collision STL;
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

Имена рабочих суставов: `joint1..joint6` и `gripper`. ROS-совместимые изменения
вносятся в `urdf/rars01.urdf`; оригинальный SolidWorks export в `source/`
сохраняется без изменений.
