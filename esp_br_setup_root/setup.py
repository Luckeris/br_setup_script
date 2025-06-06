﻿
from setuptools import setup, find_packages

setup(
    name="esp_thread_setup",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyserial",
    ],
    entry_points={
        "console_scripts": [
            "esp-thread-setup=esp_thread_setup.main:main",
        ],
    },
    author="CrackVoice & Luckeris",
    description="A utility for setting up ESP Thread Border Router and CLI devices",
    keywords="esp32, thread, border router, cli, setup",
    python_requires=">=3.6",
)
