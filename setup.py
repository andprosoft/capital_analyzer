# -*- coding: utf-8 -*-
"""
Setup script for the AP Framework.
"""

import setuptools

from python.capital_analyzer import __release__

with open("README.rst", "r") as f:
    long_description = f.read()
    
setuptools.setup(
    name="Capital Analyzer",
    version=__release__,
    author="Andriy Prots",
    author_email="andprosoft@gmail.com",
    description="Python Tool to analyze your Investments.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    #url=""
    packages=setuptools.find_packages('python'),
    package_dir={'': 'python'},
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'numpy',
        'matplotlib',
        'beautifulsoup4'
    ]
        
)

