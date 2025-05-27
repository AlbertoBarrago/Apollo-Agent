"""
Setup script for ApolloAgent.

This module uses setuptools to create a distributable package for ApolloAgent.
It reads version information from apollo/version.py.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""

from setuptools import setup, find_packages
import os
import re

with open(os.path.join("apollo", "version.py"), "r") as f:
    version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string in version.py")

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="apollo-agent",
    version=version,
    author="Alberto Barrago",
    author_email="albertobarrago@gmail.com",
    description="A custom AI agent that implements various functions for code assistance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AlbertoBarrago/Apollo-Agent",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "apollo=apollo.cli.main:main",
            "apollo-version=apollo.cli.version_info:print_version_info",
        ],
    },
)
