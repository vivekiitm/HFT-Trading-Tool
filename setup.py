from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "core",
        [
            "core/orderbook.cpp",
            "core/matching_engine.cpp",
            "core/signal_engine.cpp",
            "core/bindings.cpp",
        ],
        include_dirs=[pybind11.get_include()],
        language="c++",
    ),
]

setup(
    name="core",
    ext_modules=ext_modules,
)
