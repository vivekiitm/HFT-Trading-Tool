cmake_minimum_required(VERSION 3.14)
project(hft_core)

set(CMAKE_CXX_STANDARD 17)

find_package(pybind11 REQUIRED)

add_library(core MODULE
    core/orderbook.cpp
    core/matching_engine.cpp
    core/signal_engine.cpp
    core/bindings.cpp
)

target_link_libraries(core PRIVATE pybind11::module)
