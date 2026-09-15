cmake_minimum_required(VERSION 3.16)
project(rars01_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY meshes urdf
  DESTINATION share/${PROJECT_NAME}
)

# The go2_arm branch pins workshop_legged_gym as a submodule and reuses its
# original Unitree Go2 visual meshes.  The generated combined URDF rewrites
# those mesh paths to package://rars01_description/go2_dae/...
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/external/workshop_legged_gym/resources/robots/go2/dae")
  install(
    DIRECTORY external/workshop_legged_gym/resources/robots/go2/dae/
    DESTINATION share/${PROJECT_NAME}/go2_dae
  )
endif()

install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
  FILES_MATCHING PATTERN "*.launch.py"
)

ament_package()
