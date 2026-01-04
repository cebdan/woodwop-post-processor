"""
WoodWOP Post Processor for FreeCAD
Modular post-processor for converting FreeCAD Path operations to WoodWOP MPR 4.0 format.

This is a modular refactored version of the post-processor.
All functionality is split into separate modules for better maintainability.
"""

__version__ = "0.37-modular"
__author__ = "WoodWOP Post Processor Team"

# Note: Dev mode cache cleaning is handled in woodwop_post.py (entry point)
# to avoid circular dependencies and ensure it runs when FreeCAD loads the module

# Export main interface - lazy import to avoid FreeCAD dependency during testing
# IMPORTANT: Import directly from woodwop_post_impl, NOT from woodwop_post
# to avoid circular dependency (woodwop_post -> woodwop_post_impl -> woodwop -> woodwop_post)
def _get_exports():
    """Lazy import of main exports to avoid FreeCAD dependency during testing."""
    from .woodwop_post_impl import export, TOOLTIP, TOOLTIP_ARGS, POSTPROCESSOR_FILE_NAME, FILE_EXTENSION, UNITS, linenumber
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

