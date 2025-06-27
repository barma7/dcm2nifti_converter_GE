"""
Command-line interface for DCM2NIfTI converter.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Dict, Any

from dcm2nifti import Dicom2NiftiConverter


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='Convert DICOM files to NIfTI format for various MRI sequences.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert MESE sequence
  python -m dcm2nifti /path/to/dicoms /path/to/output mese
  
  # Convert DESS sequence  
  python -m dcm2nifti /path/to/dicoms /path/to/output dess
  
  # Convert UTE sequence with co-registration
  python -m dcm2nifti /path/to/dicoms /path/to/output ute --series_numbers 300 400 500 --coregister
  
  # Convert general multi-echo sequence
  python -m dcm2nifti /path/to/dicoms /path/to/output general_echo
  
  # Convert general multi-echo without position sorting
  python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --no_sort_by_position
  
  # List supported sequence types
  python -m dcm2nifti --list-sequences
        """
    )
    
    # Main arguments
    parser.add_argument('input_folder', nargs='?', type=str, 
                       help='Path to input DICOM folder')
    parser.add_argument('output_folder', nargs='?', type=str, 
                       help='Path to output folder')
    parser.add_argument('sequence_type', nargs='?', type=str, 
                       help='Type of sequence to convert')
    
    # Optional arguments
    parser.add_argument('--series_numbers', nargs='+', type=str, default=None,
                       help='List of series numbers to combine (for UTE, etc.)')
    parser.add_argument('--coregister', action='store_true', 
                       help='Perform co-registration (for UTE)')
    parser.add_argument('--save_echo_images', action='store_true', default=True,
                       help='Save individual echo images (for DESS)')
    parser.add_argument('--cv', type=int, default=17, 
                       help='CV value for MEGRE conversion (17 or 29)')
    parser.add_argument('--complex', action='store_true', 
                       help='Process complex data (for IDEAL)')
    parser.add_argument('--invert', action='store_true',
                       help='Invert slice order (for IDEAL)')
    parser.add_argument('--sort_by_position', action='store_true', default=True,
                       help='Sort files by spatial position (for GENERAL_ECHO)')
    parser.add_argument('--no_sort_by_position', dest='sort_by_position', action='store_false',
                       help='Do not sort files by spatial position (for GENERAL_ECHO)')
    
    # Utility arguments
    parser.add_argument('--list-sequences', action='store_true',
                       help='List supported sequence types and exit')
    parser.add_argument('--get-parameters', type=str, metavar='SEQUENCE_TYPE',
                       help='Get parameter information for a sequence type')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate input without converting')
    
    # Logging
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress all output except errors')
    parser.add_argument('--log-file', type=str,
                       help='Path to log file (default: console only)')
    
    return parser


def setup_logging(verbose: bool, quiet: bool, log_file: str = None) -> None:
    """Set up logging based on command-line options."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log file specified)
    if log_file:
        from pathlib import Path
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        print(f"Logging to file: {log_file}")


def build_conversion_kwargs(args: argparse.Namespace) -> Dict[str, Any]:
    """Build kwargs dictionary from command-line arguments."""
    kwargs = {}
    
    # Add sequence-specific parameters
    if args.series_numbers:
        kwargs['series_numbers'] = args.series_numbers
    
    if args.coregister:
        kwargs['coregister'] = True
    
    if hasattr(args, 'save_echo_images'):
        kwargs['save_echo_images'] = args.save_echo_images
    
    if args.cv != 17:
        kwargs['cv'] = args.cv
    
    if args.complex:
        kwargs['complex'] = True
    
    if args.invert:
        kwargs['invert'] = True
    
    # General echo parameters
    if hasattr(args, 'sort_by_position'):
        kwargs['sort_by_position'] = args.sort_by_position
    
    return kwargs


def list_sequences(converter: Dicom2NiftiConverter) -> None:
    """List supported sequence types."""
    sequences = converter.list_supported_sequences()
    
    print("Supported sequence types:")
    print("=" * 30)
    
    for seq_type in sorted(sequences):
        print(f"  {seq_type.upper()}")
        
        # Get parameter info
        try:
            params = converter.get_sequence_parameters(seq_type)
            if params['required']:
                print(f"    Required: {', '.join(params['required'])}")
            if params['optional']:
                print(f"    Optional: {', '.join(params['optional'])}")
        except Exception:
            pass
        
        print()


def get_parameters(converter: Dicom2NiftiConverter, sequence_type: str) -> None:
    """Get parameter information for a sequence type."""
    try:
        params = converter.get_sequence_parameters(sequence_type)
        
        print(f"Parameters for {sequence_type.upper()} sequence:")
        print("=" * 40)
        
        print("Required parameters:")
        for param in params['required']:
            print(f"  - {param}")
        
        print("\nOptional parameters:")
        for param in params['optional']:
            print(f"  - {param}")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def validate_required_args(args: argparse.Namespace) -> None:
    """Validate that required arguments are provided."""
    if not args.list_sequences and not args.get_parameters:
        if not all([args.input_folder, args.output_folder, args.sequence_type]):
            print("Error: input_folder, output_folder, and sequence_type are required")
            sys.exit(1)


def main() -> None:
    """Main entry point for command-line interface."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose, args.quiet, getattr(args, 'log_file', None))
    
    # Create converter
    converter = Dicom2NiftiConverter()
    
    # Handle utility commands
    if args.list_sequences:
        list_sequences(converter)
        return
    
    if args.get_parameters:
        get_parameters(converter, args.get_parameters)
        return
    
    # Validate required arguments
    validate_required_args(args)
    
    # Build conversion parameters
    kwargs = build_conversion_kwargs(args)
    
    try:
        if args.validate_only:
            # Only validate input
            print(f"Validating {args.sequence_type.upper()} conversion...")
            converter.validate_conversion(args.sequence_type, args.input_folder, **kwargs)
            print("✓ Validation successful!")
        else:
            # Perform full conversion
            print(f"Starting {args.sequence_type.upper()} conversion...")
            result = converter.convert(args.sequence_type, args.input_folder, args.output_folder, **kwargs)
            
            print("✓ Conversion completed successfully!")
            print(f"Generated {len(result.output_files)} output files:")
            for file_path in result.output_files:
                print(f"  - {file_path}")
    
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
