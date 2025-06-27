"""
DCM2NIfTI: A modular DICOM to NIfTI converter for various MRI sequences.
"""

__version__ = "2.0.0"
__author__ = "Marco Barbieri"

from .core import Dicom2NiftiConverter
from .base import SequenceConverter, ConversionResult

__all__ = ['Dicom2NiftiConverter', 'SequenceConverter', 'ConversionResult']
