# Архитектура `rars01_description`

## Назначение

`rars01_description` — отдельный ROS 2 description package. Он является
единственным источником геометрии RARS01, дерева звеньев, осей суставов,
кинематических пределов, масс и инерций.

```text
SolidWorks export
      │ ручная проверка и нормализация
      ▼
urdf/rars01.urdf + meshes/
      │
      ├── robot_state_publisher
      ├── RViz
      ├── MoveIt
      └── будущий Gazebo
```

## Рабочие файлы ROS 2

- `urdf/rars01.urdf` — каноническая модель, которую должны подключать
  MoveIt, RViz и `robot_state_publisher`.
- `meshes/` — девять рабочих STL-моделей звеньев, на которые ссылается
  канонический URDF.
- `launch/display.launch.py` — автономный просмотр модели через
  `robot_state_publisher`, `joint_state_publisher_gui` и RViz.
- `CMakeLists.txt` — устанавливает `urdf`, `meshes` и ROS 2 launch-файлы.
- `package.xml` — метаданные и runtime-зависимости ROS 2.
- `README.md` — сборка, просмотр и правила обновления модели.
- `LICENSE` — лицензия репозитория.

## Исходный экспорт SolidWorks

Каталог `source/solidworks_export/` хранит входные материалы и не должен
подключаться рабочими launch-файлами напрямую:

- `urdf/RARS01_1.urdf` — исходный автоматически экспортированный URDF;
- `urdf/RARS01_1.csv` — таблица параметров экспорта;
- `config/joint_names_RARS01_1.yaml` — исходное соответствие имён суставов;
- `launch/display.launch` — старый ROS 1 launch от экспортёра;
- `launch/gazebo.launch` — старый ROS 1/Gazebo launch от экспортёра;
- `meshes/` — исходные CAD meshes;
- `export.log` — журнал экспортёра.

Файл `rewrite_description` фиксирует происхождение/правила переработки
экспортированной модели. При новом экспорте сначала обновляется каталог
`source`, затем изменения осознанно переносятся в `urdf/rars01.urdf` и
`meshes/`.

## Границы ответственности

Пакет содержит физическое описание робота, но не содержит:

- serial/CAN-протокол;
- `Kp/Kd`, `direction` и калибровочные `zero_offset`;
- `ros2_control` hardware plugin;
- SRDF, OMPL и настройки MoveIt;
- launch реального оборудования.

Калибровка конкретного экземпляра находится в
`reBotArmController_ROS2/src/rebotarm_bringup/config/rars01_hardware.yaml`.
MoveIt-конфигурация находится в пакете `rebotarm_moveit_config`.

Генерируемые `build`, `install` и `log` не являются исходниками и не должны
попадать в Git.
