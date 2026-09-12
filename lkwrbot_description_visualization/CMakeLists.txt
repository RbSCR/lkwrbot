cmake_minimum_required(VERSION 3.28.3)
project(lkwrbot_description_visualization)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

find_package(urdf REQUIRED)
find_package(xacro REQUIRED)
find_package(lkwrbot_description REQUIRED)

install(
  DIRECTORY rviz2 launch
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # Linters to be used in the 'auto-linting' are mentioned in package.xml

  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
