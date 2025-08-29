"""
Setup script for encos_sdk package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="encos_sdk",
    version="1.0.0",
    author="Dyna Team",
    author_email="support@dyna.com",
    description="一个完整的电机控制软件开发工具包(SDK)，基于CAN总线通信协议",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dyna/encos_sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.7",
    install_requires=[
        "python-can>=4.0.0",
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "encos-cli=encos_sdk.cli_tool:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="motor control CAN bus SDK robotics automation",
)
