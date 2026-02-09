# cmake_minimum_required(VERSION 3.15)
# project(test_package CXX)

# find_package(MAVSDK REQUIRED)

# add_executable(test_pkg test_package.cpp)
# target_link_libraries(test_pkg PRIVATE MAVSDK::MAVSDK)


cmake_minimum_required(VERSION 3.21)
project(test_package LANGUAGES CXX)
find_package(MAVSDK CONFIG REQUIRED)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

file(GLOB_RECURSE APP_SOURCES CONFIGURE_DEPENDS src/*.cpp)
file(GLOB_RECURSE APP_HEADERS include/*.h include/*.hpp)

add_executable(
	test_pkg test_package.cpp 
	${APP_SOURCES}
	${APP_HEADERS}
)
target_link_libraries(
	test_pkg 
	PRIVATE	MAVSDK::MAVSDK
)

target_include_directories(test_pkg
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

set_target_properties(
	test_pkg 
	PROPERTIES
    OUTPUT_NAME "test_pkg"
)