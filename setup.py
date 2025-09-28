"""Setup script for micktrace."""

from setuptools import setup, find_packages

setup(
    name="micktrace",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "aioboto3>=11.3.0",
        "botocore>=1.31.62",
        "azure-monitor-ingestion>=1.0.0b5",
        "azure-core>=1.29.5",
        "google-cloud-logging>=3.8.0",
        "typing-extensions>=4.0.0"
    ],
    description="The world's most advanced Python logging library",
    author="Ajay Agrawal",
    author_email="ajay@micktrace.dev",
    url="https://github.com/ajayagrawalgit/micktrace",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: Software Development :: Debuggers",
        "Typing :: Typed",
        "Environment :: Console",
        "Framework :: AsyncIO"
    ]
)
