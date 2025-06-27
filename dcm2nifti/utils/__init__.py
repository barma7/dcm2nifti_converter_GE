"""
Utility functions and classes.
"""

from .dicom_utils import (
    copy_image_headers,
    get_slice_thickness,
    sort_dicom_files_by_position,
    analyze_dicom_series,
    validate_dicom_series
)

from .image_utils import (
    sitk_image_from_array,
    create_4d_direction_matrix,
    whiten_image,
    register_volumes,
    apply_transform,
    calculate_porosity_index,
    calculate_saturation_recovery_index,
    calculate_complex_magnitude
)

from .file_utils import (
    save_nifti_image,
    save_metadata,
    load_metadata,
    save_conversion_summary,
    create_nibabel_image,
    validate_output_files
)

__all__ = [
    # dicom_utils
    'copy_image_headers',
    'get_slice_thickness',
    'sort_dicom_files_by_position',
    'analyze_dicom_series',
    'validate_dicom_series',
    
    # image_utils
    'sitk_image_from_array',
    'create_4d_direction_matrix',
    'whiten_image',
    'register_volumes',
    'apply_transform',
    'calculate_porosity_index',
    'calculate_saturation_recovery_index',
    'calculate_complex_magnitude',
    
    # file_utils
    'save_nifti_image',
    'save_metadata',
    'load_metadata',
    'save_conversion_summary',
    'create_nibabel_image',
    'validate_output_files'
]
