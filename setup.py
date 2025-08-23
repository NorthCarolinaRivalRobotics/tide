#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="tide-sdk",
    version="0.1.8",
    description="A Zenoh-based robotics framework with opinionated namespacing",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Tide Team",
    python_requires=">=3.12",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "tide": [
            "cli/templates/*.template",
            "cli/templates/config/*",
            "cli/templates/nodes/*",
        ],
    },
    install_requires=[
        "eclipse-zenoh>=1.3.4",
        "hypothesis>=6.131.15",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "rich>=13.6.0",
    ],
    entry_points={
        "console_scripts": [
            "tide=tide.cli:main",
        ],
    },
) 