"""
Setup script for dcm2nifti package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file with UTF-8 encoding
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

setup(
    name="dcm2nifti_converter_GE",
    version="2.0.0",
    author="Marco Barbieri",
    author_email="",
    description="A modular DICOM to NIfTI converter for various GE MRI sequences",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/barma7/dcm2nifti_converter_GE",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Image Analysis",
    ],
    python_requires=">=3.10",
    install_requires=[
        "simpleitk-simpleelastix>=2.5.0",
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
