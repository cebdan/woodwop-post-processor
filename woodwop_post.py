"""
WoodWOP Post Processor for FreeCAD - Entry Point
This file is the entry point for FreeCAD. It imports the modular post-processor.
"""

# FreeCAD expects a file named woodwop_post.py in the post-processor directory
# This file imports the modular version from the woodwop package

import os
import sys
import importlib.util

# Add parent directory to path to allow importing from woodwop package
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# CRITICAL: Apply patches to Command.py automatically
# The patch modules are self-contained and handle everything automatically
# They will apply patches when FreeCAD modules become available
def _ensure_command_patch():
    """Ensure patches are applied to Command.py when FreeCAD is available."""
    try:
        import importlib.util
        
        # Apply command_patch (for gcode type fix)
        patch_path = os.path.join(_current_dir, 'command_patch.py')
        if os.path.exists(patch_path):
            spec = importlib.util.spec_from_file_location("command_patch", patch_path)
            if spec and spec.loader:
                patch_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(patch_module)
                # Use ensure_patch_applied() which is safe to call multiple times
                if hasattr(patch_module, 'ensure_patch_applied'):
                    patch_module.ensure_patch_applied()
                elif hasattr(patch_module, 'apply_patch'):
                    patch_module.apply_patch()
        
        # Apply dialog_patch (for .mpr extension enforcement)
        # TEMPORARILY DISABLED due to Qt import issues
        # FreeCAD will use .mpr extension based on subpart='mpr' from export() return value
        # dialog_patch_path = os.path.join(_current_dir, 'dialog_patch.py')
        # if os.path.exists(dialog_patch_path):
        #     spec = importlib.util.spec_from_file_location("dialog_patch", dialog_patch_path)
        #     if spec and spec.loader:
        #         dialog_patch_module = importlib.util.module_from_spec(spec)
        #         spec.loader.exec_module(dialog_patch_module)
        #         # Use ensure_dialog_patch_applied() which is safe to call multiple times
        #         if hasattr(dialog_patch_module, 'ensure_dialog_patch_applied'):
        #             dialog_patch_module.ensure_dialog_patch_applied()
        #         elif hasattr(dialog_patch_module, 'apply_dialog_patch'):
        #             dialog_patch_module.apply_dialog_patch()
        
        return True
    except Exception as e:
        # Patch failed - log but don't fail
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning(
                f"WoodWOP: Failed to ensure Command.py patches: {e}\n"
            )
        except:
            pass
    return False

# Try to apply patch immediately (if FreeCAD is already loaded)
# The patch module will handle this automatically, but we try here too
try:
    import FreeCAD
    _ensure_command_patch()
except:
    # FreeCAD not loaded yet - patch will be applied automatically when needed
    # The patch module is self-contained and will apply itself when FreeCAD loads
    pass

# Import from the modular structure
# Direct import from same directory (FreeCAD loads this file directly)
impl_path = os.path.join(_current_dir, 'woodwop_post_impl.py')
if os.path.exists(impl_path):
    spec = importlib.util.spec_from_file_location("woodwop_post_impl", impl_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        export = module.export
        TOOLTIP = module.TOOLTIP
        TOOLTIP_ARGS = module.TOOLTIP_ARGS
        POSTPROCESSOR_FILE_NAME = module.POSTPROCESSOR_FILE_NAME
        FILE_EXTENSION = module.FILE_EXTENSION
        UNITS = module.UNITS
        linenumber = module.linenumber
    else:
        raise ImportError("Could not load woodwop_post_impl module")
else:
    raise ImportError(f"woodwop_post_impl.py not found at {impl_path}")

# Re-export for FreeCAD compatibility
__all__ = ['export', 'TOOLTIP', 'TOOLTIP_ARGS', 'POSTPROCESSOR_FILE_NAME', 'FILE_EXTENSION', 'UNITS', 'linenumber']
