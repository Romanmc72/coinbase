#!/usr/bin/env python3
from setuptools import find_packages, setup

setup(
    name="cb",
    packages=find_packages("src"),
    package_dir={"": "src"},
)
