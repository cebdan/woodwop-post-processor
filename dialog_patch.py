"""
WoodWOP Dialog Patch Module
This module patches FreeCAD's Command.py _write_file method to ensure
MPR files always use .mpr extension in the file dialog.

NOTE: This patch is currently COMPLETELY DISABLED due to Qt import issues.
FreeCAD will use .mpr extension based on subpart='mpr' from export() return value.
"""

import os
import inspect

# Try to import FreeCAD modules
FreeCAD = None
QtGui = None
QtWidgets = None
QFileDialog = None
CommandPathPost = None
Path = None

# PATCH DISABLED - Set flag to disable dialog patch
DISABLE_DIALOG_PATCH = True

try:
    import FreeCAD
    # Don't import QtGui/QtWidgets at module level - import lazily in _get_qfile_dialog()
    # This prevents import errors when module is loaded
    QtGui = None
    QtWidgets = None
    QFileDialog = None
    
    import Path
    
    # Try different import paths for Command class
    try:
        from PathScripts.PathPost.Command import CommandPathPost
    except ImportError:
        try:
            from Path.Post.Command import CommandPathPost
        except ImportError:
            try:
                import Path.Post.Command as CommandModule
                CommandPathPost = getattr(CommandModule, 'CommandPathPost', None)
            except ImportError:
                CommandPathPost = None
except ImportError:
    # FreeCAD not available - this is OK for testing
    pass


def _get_qfile_dialog():
    """Get QFileDialog class safely."""
    global QFileDialog, QtGui, QtWidgets
    
    if QFileDialog is not None:
        return QFileDialog
    
    # Try to import if not already imported
    # Use a completely isolated approach to avoid any import errors
    
    # Try PySide2 first (most common)
    try:
        import sys
        # Check if already in sys.modules
        if 'PySide2.QtWidgets' in sys.modules:
            mod = sys.modules['PySide2.QtWidgets']
            if hasattr(mod, 'QFileDialog'):
                QFileDialog = mod.QFileDialog
                QtWidgets = mod
                QtGui = None
                return QFileDialog
        
        # Try fresh import
        mod = __import__('PySide2.QtWidgets', fromlist=['QFileDialog'], level=0)
        if hasattr(mod, 'QFileDialog'):
            QFileDialog = getattr(mod, 'QFileDialog')
            QtWidgets = mod
            QtGui = None
            return QFileDialog
    except Exception:
        # Silently continue to next option
        pass
    
    # Try PySide6
    try:
        import sys
        if 'PySide6.QtWidgets' in sys.modules:
            mod = sys.modules['PySide6.QtWidgets']
            if hasattr(mod, 'QFileDialog'):
                QFileDialog = mod.QFileDialog
                QtWidgets = mod
                QtGui = None
                return QFileDialog
        
        mod = __import__('PySide6.QtWidgets', fromlist=['QFileDialog'], level=0)
        if hasattr(mod, 'QFileDialog'):
            QFileDialog = getattr(mod, 'QFileDialog')
            QtWidgets = mod
            QtGui = None
            return QFileDialog
    except Exception:
        pass
    
    # Try old PySide (QtGui.QFileDialog)
    try:
        import sys
        if 'PySide.QtGui' in sys.modules:
            mod = sys.modules['PySide.QtGui']
            if hasattr(mod, 'QFileDialog'):
                QFileDialog = mod.QFileDialog
                QtGui = mod
                QtWidgets = None
                return QFileDialog
        
        mod = __import__('PySide.QtGui', fromlist=['QFileDialog'], level=0)
        if hasattr(mod, 'QFileDialog'):
            QFileDialog = getattr(mod, 'QFileDialog')
            QtGui = mod
            QtWidgets = None
            return QFileDialog
    except Exception:
        pass
    
    return None


def _create_patched_write_file(original_method):
    """Create a patched version of _write_file method with MPR extension enforcement."""
    
    # PATCH COMPLETELY DISABLED - Always call original method
    # This prevents any Qt import issues or other errors
    def patched_write_file(self, filename, gcode, policy, generator=None):
        """
        Patched version of _write_file that ensures MPR files always use .mpr extension.
        
        NOTE: This patch is currently COMPLETELY DISABLED - it just calls the original method.
        FreeCAD will use .mpr extension based on subpart='mpr' from export() return value.
        """
        # ALWAYS call original method - patch is completely disabled
        sig = inspect.signature(original_method)
        params = list(sig.parameters.keys())
        if 'generator' in params:
            return original_method(self, filename, gcode, policy, generator)
        else:
            return original_method(self, filename, gcode, policy)
    
    # Mark as patched
    patched_write_file._woodwop_dialog_patched = True
    patched_write_file._woodwop_original = original_method
    
    return patched_write_file


def apply_dialog_patch():
    """
    Apply monkey patch to Command.py's _write_file method to enforce .mpr extension.
    This should be called when the post-processor is loaded.
    Works with existing command_patch if it's already applied.
    
    NOTE: This patch is currently DISABLED due to Qt import issues.
    """
    # PATCH DISABLED - Return immediately
    if DISABLE_DIALOG_PATCH:
        return False
    
    if CommandPathPost is None:
        if FreeCAD:
            FreeCAD.Console.PrintWarning(
                "WoodWOP Dialog Patch: CommandPathPost class not found, cannot apply patch\n"
            )
        return False

    # CRITICAL: Test if QFileDialog can be imported before applying patch
    # This prevents errors during patch application
    test_qfile_dialog = _get_qfile_dialog()
    if test_qfile_dialog is None:
        if FreeCAD:
            FreeCAD.Console.PrintWarning(
                "WoodWOP Dialog Patch: QFileDialog not available, skipping dialog patch\n"
            )
        return False

    try:
        # Check if patch is already applied
        if hasattr(CommandPathPost, '_write_file') and \
           hasattr(CommandPathPost._write_file, '_woodwop_dialog_patched'):
            # Patch already applied
            if FreeCAD:
                FreeCAD.Console.PrintMessage("WoodWOP Dialog Patch: Patch already applied\n")
            return True

        # Get the current method (may already be patched by command_patch)
        if not hasattr(CommandPathPost, '_write_file'):
            if FreeCAD:
                FreeCAD.Console.PrintError(
                    "WoodWOP Dialog Patch: CommandPathPost._write_file method not found\n"
                )
            return False

        current_write_file = CommandPathPost._write_file
        
        # If method is already patched by command_patch, get the original
        # Otherwise, use current method as original
        if hasattr(current_write_file, '_woodwop_original'):
            original_write_file = current_write_file._woodwop_original
        elif hasattr(current_write_file, '_woodwop_patched'):
            # This is from command_patch, get its original
            original_write_file = getattr(current_write_file, '_woodwop_original', current_write_file)
        else:
            original_write_file = current_write_file

        # Create patched method (this will wrap both patches)
        patched_method = _create_patched_write_file(original_write_file)
        
        # Preserve any existing patches
        if hasattr(current_write_file, '_woodwop_patched'):
            patched_method._woodwop_patched = True
            patched_method._woodwop_original = original_write_file

        # Replace the method
        CommandPathPost._write_file = patched_method

        if FreeCAD:
            FreeCAD.Console.PrintMessage(
                "WoodWOP Dialog Patch: Applied dialog patch to Command.py _write_file method\n"
            )

        return True
    except Exception as e:
        if FreeCAD:
            FreeCAD.Console.PrintError(
                f"WoodWOP Dialog Patch: Failed to apply dialog patch: {e}\n"
            )
            import traceback
            FreeCAD.Console.PrintError(f"Traceback: {traceback.format_exc()}\n")
        return False


def ensure_dialog_patch_applied():
    """
    Ensure dialog patch is applied. This is a convenience function that can be called
    multiple times safely.
    
    NOTE: This patch is currently DISABLED due to Qt import issues.
    """
    # PATCH DISABLED - Return immediately
    if DISABLE_DIALOG_PATCH:
        return False
    return apply_dialog_patch()
