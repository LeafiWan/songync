#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = [
    'beautifulsoup4',
    'setuptools',
    'requests>=2.0.0'
]

entry_points = """
[console_scripts]
"""

setup(
    name="songync",
    version="0.0.1",
    url='',
    license='WTFPL',
    description="Sync your favovite songs between serveral music sites.",
    author='psjay.peng@gmail.com',
    packages=find_packages(),
    install_requires=install_requires,
    entry_points=entry_points,
)
