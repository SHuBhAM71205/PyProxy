from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension(
            "pyproxy_native",
            ["wrapper.cpp", "ProxyCore/proxy.cpp"],
            extra_compile_args=["/std:c++20"],
        )
    ]
)
