"""
Setup script for dcm2nifti package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="dcm2nifti-refactored",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A modular DICOM to NIfTI converter for various MRI sequences",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/dcm2nifti-refactored",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    python_requires=">=3.8",
    install_requires=[
        "SimpleITK>=2.0.0",
        "pydicom>=2.0.0",
        "nibabel>=3.0.0",
        "numpy>=1.19.0",
        "pathlib2>=2.3.0; python_version<'3.6'",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "dcm2nifti=dcm2nifti.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
