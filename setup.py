from setuptools import setup, find_packages

setup(
    name="openbikesensor-proto",
    version="0.0.1",
    author="OpenBikeSensor Contributors",
    license="LGPL-3.0",
    description="OpenBikeSensor Protocol",
    url="https://github.com/openbikesensor/proto",
    packages=find_packages(),
    package_data={},
    install_requires=[
        "protobuf~=4.21.12",
        "cobs~=1.2.0",
        "pyserial>=3.5,<=3.6",
    ],
    entry_points={
        "console_scripts": [
            "openbikesensor-convert=obs.bin.openbikesensor_convert:main",
        ]
    },
)
