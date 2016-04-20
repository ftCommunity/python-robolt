#!/usr/bin/env python

import os
from setuptools import setup, find_packages

setup(
    name='robolt',
    version='1.0.0',
    packages=find_packages(),
    install_requires=['pyusb'],
    zip_safe=False,
    include_package_data=True,
    author="Till Harbaum",
    author_email="till@harbaum.org",
    description="This is a python library for the Fischertechnik RoboLT interface.",
    license="GPL",
    keywords="fischertechnik txt robolt motor sensor driver",
    url="https://github.com/ftCommunity/python-robolt",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2"]
)
