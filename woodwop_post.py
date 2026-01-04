"""
WoodWOP Post Processor for FreeCAD - Entry Point
This file is the entry point for FreeCAD. It imports the modular post-processor.
"""

# FreeCAD expects a file named woodwop_post.py in the post-processor directory
# This file imports the modular version from the woodwop package

import os
import sys
import importlib.util
import glob
import shutil

# Development mode: Auto-clean cache on module load
# Set WOODWOP_DEV_MODE=1 environment variable to enable
# Or create a file named .dev_mode in the module directory
_current_dir = os.path.dirname(os.path.abspath(__file__))
_dev_mode_file = os.path.join(_current_dir, '.dev_mode')
_DEV_MODE = os.environ.get('WOODWOP_DEV_MODE', '0') == '1' or os.path.exists(_dev_mode_file)

if _DEV_MODE:
    # Use a flag to ensure cache is cleaned only once per session
    _cache_cleaned_flag = f"_woodwop_cache_cleaned_{_current_dir}"
    if not hasattr(sys, _cache_cleaned_flag):
        # Clean .pyc files
        pyc_files = glob.glob(os.path.join(_current_dir, '*.pyc'))
        for f in pyc_files:
            try:
                os.remove(f)
            except (OSError, PermissionError):
                pass
        
        # Clean __pycache__ directories
        pycache_dirs = glob.glob(os.path.join(_current_dir, '__pycache__'))
        for d in pycache_dirs:
            try:
                shutil.rmtree(d)
            except (OSError, PermissionError):
                pass
        
        # Also clean __pycache__ in subdirectories
        for root, dirs, files in os.walk(_current_dir):
            pycache_path = os.path.join(root, '__pycache__')
            if os.path.exists(pycache_path):
                try:
                    shutil.rmtree(pycache_path)
                except (OSError, PermissionError):
                    pass
        
        # Remove only woodwop modules from sys.modules (but not woodwop_post itself to avoid recursion)
        modules_to_remove = [
            name for name in sys.modules.keys() 
            if name.startswith('woodwop') and name != 'woodwop_post'
        ]
        for module_name in modules_to_remove:
            try:
                del sys.modules[module_name]
            except KeyError:
                pass
        
        # Mark as cleaned
        setattr(sys, _cache_cleaned_flag, True)
        
        try:
            import FreeCAD  # noqa: F401
            FreeCAD.Console.PrintMessage(f"[WoodWOP DEV] Cache cleaned in {_current_dir}\n")
        except ImportError:
            print(f"[WoodWOP DEV] Cache cleaned in {_current_dir}")

# Add parent directory to path to allow importing from woodwop package
# _current_dir already defined above for dev mode
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
