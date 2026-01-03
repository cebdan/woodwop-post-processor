"""
WoodWOP Post Processor for FreeCAD
Modular post-processor for converting FreeCAD Path operations to WoodWOP MPR 4.0 format.

This is a modular refactored version of the post-processor.
All functionality is split into separate modules for better maintainability.
"""

__version__ = "0.37-modular"
__author__ = "WoodWOP Post Processor Team"

# Development mode: Auto-clean cache on module load
# Set WOODWOP_DEV_MODE=1 environment variable to enable
# Or create a file named .dev_mode in the module directory
import os
import sys

_module_dir = os.path.dirname(os.path.abspath(__file__))
_dev_mode_file = os.path.join(_module_dir, '.dev_mode')
_DEV_MODE = os.environ.get('WOODWOP_DEV_MODE', '0') == '1' or os.path.exists(_dev_mode_file)

if _DEV_MODE:
    import glob
    import shutil
    
    # Clean .pyc files
    pyc_files = glob.glob(os.path.join(_module_dir, '*.pyc'))
    for f in pyc_files:
        try:
            os.remove(f)
        except:
            pass
    
    # Clean __pycache__ directories
    pycache_dirs = glob.glob(os.path.join(_module_dir, '__pycache__'))
    for d in pycache_dirs:
        try:
            shutil.rmtree(d)
        except:
            pass
    
    # Also clean __pycache__ in subdirectories
    for root, dirs, files in os.walk(_module_dir):
        pycache_path = os.path.join(root, '__pycache__')
        if os.path.exists(pycache_path):
            try:
                shutil.rmtree(pycache_path)
            except:
                pass
    
    print(f"[WoodWOP DEV] Cache cleaned in {_module_dir}")

# Export main interface - lazy import to avoid FreeCAD dependency during testing
def _get_exports():
    """Lazy import of main exports to avoid FreeCAD dependency during testing."""
    from .woodwop_post import export, TOOLTIP, TOOLTIP_ARGS, POSTPROCESSOR_FILE_NAME, FILE_EXTENSION, UNITS, linenumber
    return {
        'export': export,
        'TOOLTIP': TOOLTIP,
        'TOOLTIP_ARGS': TOOLTIP_ARGS,
        'POSTPROCESSOR_FILE_NAME': POSTPROCESSOR_FILE_NAME,
        'FILE_EXTENSION': FILE_EXTENSION,
        'UNITS': UNITS,
        'linenumber': linenumber,
    }

# Try to import, but don't fail if FreeCAD is not available
try:
    _exports = _get_exports()
    export = _exports['export']
    TOOLTIP = _exports['TOOLTIP']
    TOOLTIP_ARGS = _exports['TOOLTIP_ARGS']
    POSTPROCESSOR_FILE_NAME = _exports['POSTPROCESSOR_FILE_NAME']
    FILE_EXTENSION = _exports['FILE_EXTENSION']
    UNITS = _exports['UNITS']
    linenumber = _exports['linenumber']
except ImportError:
    # FreeCAD not available - this is OK for testing
    export = None
    TOOLTIP = None
    TOOLTIP_ARGS = None
    POSTPROCESSOR_FILE_NAME = None
    FILE_EXTENSION = None
    UNITS = None
    linenumber = None

__all__ = [
    'export',
    'TOOLTIP',
    'TOOLTIP_ARGS',
    'POSTPROCESSOR_FILE_NAME',
    'FILE_EXTENSION',
    'UNITS',
    'linenumber',
]

