"""
WoodWOP Command Patch Module
This module patches FreeCAD's Command.py to fix the gcode type issue.
It uses monkey patching to replace the _write_file method with a fixed version.
This module is self-contained and applies the patch automatically when needed.
"""

import os

# Global flag to track if patch is applied
_patch_applied = False
_original_write_file = None

# Try to import FreeCAD modules (may not be available during testing)
FreeCAD = None
CommandPathPost = None

def _import_freecad_modules():
    """Import FreeCAD modules when available."""
    global FreeCAD, CommandPathPost
    
    if FreeCAD is not None and CommandPathPost is not None:
        return True
    
    try:
        import FreeCAD as FC
        FreeCAD = FC
        
        # Try different import paths for Command class
        try:
            from PathScripts.PathPost.Command import CommandPathPost as CP
            CommandPathPost = CP
        except ImportError:
            try:
                from Path.Post.Command import CommandPathPost as CP
                CommandPathPost = CP
            except ImportError:
                try:
                    import Path.Post.Command as CommandModule
                    CommandPathPost = getattr(CommandModule, 'CommandPathPost', None)
                except ImportError:
                    CommandPathPost = None
        
        return CommandPathPost is not None
    except ImportError:
        # FreeCAD not available - this is OK for testing
        return False


def _create_patched_method(original_method):
    """Create a patched version of _write_file method."""
    
    def patched_write_file(self, filename, gcode, policy, generator=None):
        """
        Patched version of _write_file that ensures gcode is always a string.
        
        This fixes the issue where gcode might be a list instead of a string,
        causing "write() argument must be str, not list" error.
        """
        # CRITICAL: Ensure gcode is a string before any operations
        if not isinstance(gcode, str):
            gcode_type = type(gcode).__name__
            if FreeCAD:
                FreeCAD.Console.PrintError(
                    f"WoodWOP Patch: gcode is not a string! Type: {gcode_type}, "
                    f"filename: {filename}\n"
                )
                FreeCAD.Console.PrintError(
                    f"WoodWOP Patch: gcode value (first 200 chars): "
                    f"{repr(gcode)[:200]}\n"
                )
            
            # Force conversion to string
            if isinstance(gcode, list):
                if FreeCAD:
                    FreeCAD.Console.PrintError(
                        f"WoodWOP Patch: gcode is a list with {len(gcode)} items, "
                        f"converting to string...\n"
                    )
                
                # Handle list of tuples (result from export function)
                if len(gcode) > 0 and isinstance(gcode[0], tuple):
                    # This is the result from export() - extract content from first tuple
                    if FreeCAD:
                        FreeCAD.Console.PrintError(
                            "WoodWOP Patch: gcode is a list of tuples, "
                            "extracting content from first tuple...\n"
                        )
                    if len(gcode[0]) >= 2:
                        gcode = gcode[0][1]  # Get content from first tuple
                        # If content is still not a string, convert it
                        if not isinstance(gcode, str):
                            if isinstance(gcode, list):
                                gcode = '\n'.join(str(item) for item in gcode)
                            else:
                                gcode = str(gcode) if gcode else ""
                    else:
                        gcode = '\n'.join(str(item) for item in gcode)
                else:
                    gcode = '\n'.join(str(item) for item in gcode)
            else:
                gcode = str(gcode) if gcode else ""
            
            if FreeCAD:
                FreeCAD.Console.PrintError(
                    f"WoodWOP Patch: After conversion: type={type(gcode).__name__}, "
                    f"length={len(gcode)}\n"
                )
        
        # CRITICAL: Check if this is MPR content and use custom dialog
        is_mpr = False
        if isinstance(gcode, str) and len(gcode) > 0:
            # Check if this is MPR content
            if gcode.strip().startswith('[H'):
                # Check for MPR signature
                if 'VERSION=' in gcode or 'WW=' in gcode:
                    is_mpr = True
        
        # Use beautiful custom dialog for MPR files when policy is "open file dialog"
        # Only use custom dialog if GUI is available
        if is_mpr and policy and policy.casefold() == "open file dialog":
            # Check if GUI is available
            gui_available = False
            try:
                if FreeCAD and hasattr(FreeCAD, 'GuiUp'):
                    gui_available = FreeCAD.GuiUp
            except:
                pass
            
            if gui_available:
                try:
                    # Import our custom dialog module
                    import importlib.util
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    dialog_path = os.path.join(current_dir, 'woodwop_file_dialog.py')
                    
                    if os.path.exists(dialog_path):
                        spec = importlib.util.spec_from_file_location("woodwop_file_dialog", dialog_path)
                        if spec and spec.loader:
                            dialog_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(dialog_module)
                            
                            # Get default directory and filename
                            default_dir = os.path.dirname(filename) if filename else ""
                            default_name = os.path.basename(filename) if filename else "output.mpr"
                            
                            # Show beautiful dialog
                            selected_file = dialog_module.show_save_dialog(
                                parent=None,
                                default_filename=default_name,
                                default_directory=default_dir
                            )
                            
                            if selected_file:
                                # User selected a file - write it
                                filename = selected_file
                                # CRITICAL: Use binary mode to prevent Python from converting \n to \r\n
                                # newline="\r\n" causes Python to replace \n with \r\n, resulting in \r\r\n
                                # Binary mode writes data exactly as-is without any line ending conversion
                                with open(filename, "wb") as f:
                                    f.write(gcode.encode("cp1252", errors="replace"))
                                
                                if FreeCAD:
                                    FreeCAD.Console.PrintMessage(f"File written to {filename}\n")
                                
                                if generator:
                                    generator.log(f"    File written successfully: '{filename}'")
                                
                                return filename
                            else:
                                # User cancelled
                                if generator:
                                    generator.log("    User cancelled file dialog", "WARNING")
                                return None
                except Exception as e:
                    # Fallback to original method if custom dialog fails
                    if FreeCAD:
                        FreeCAD.Console.PrintWarning(
                            f"WoodWOP: Custom dialog failed, using default: {e}\n"
                        )
                    # Continue to original method below
        
        # Replace file extension to .mpr if content is MPR format (for non-dialog policies)
        if is_mpr:
            base_name, ext = os.path.splitext(filename)
            if ext.lower() != '.mpr':
                filename = base_name + '.mpr'
                if FreeCAD:
                    FreeCAD.Console.PrintMessage(
                        f"WoodWOP Patch: Replaced extension to .mpr: {filename}\n"
                    )
        
        # Call the original method with the fixed gcode
        # Check if original method accepts generator parameter
        import inspect
        try:
            sig = inspect.signature(original_method)
            params = list(sig.parameters.keys())
            if 'generator' in params:
                return original_method(self, filename, gcode, policy, generator)
            else:
                return original_method(self, filename, gcode, policy)
        except Exception:
            # Fallback: try with generator first, then without
            try:
                return original_method(self, filename, gcode, policy, generator)
            except TypeError:
                return original_method(self, filename, gcode, policy)
    
    # Mark as patched
    patched_write_file._woodwop_patched = True
    patched_write_file._woodwop_original = original_method
    
    return patched_write_file


def apply_patch(force=False):
    """
    Apply monkey patch to Command.py's _write_file method.
    
    This function is idempotent - it can be called multiple times safely.
    The patch is applied automatically when the module is imported and
    FreeCAD is available.
    
    Args:
        force: If True, reapply patch even if already applied
        
    Returns:
        bool: True if patch was applied successfully, False otherwise
    """
    global _patch_applied, _original_write_file
    
    # Try to import FreeCAD modules
    if not _import_freecad_modules():
        # FreeCAD not available - can't apply patch
        return False
    
    if CommandPathPost is None:
        if FreeCAD:
            FreeCAD.Console.PrintWarning(
                "WoodWOP Patch: CommandPathPost class not found, cannot apply patch\n"
            )
        return False
    
    try:
        # Check if patch is already applied by checking the method attribute
        if hasattr(CommandPathPost, '_write_file') and \
           hasattr(CommandPathPost._write_file, '_woodwop_patched'):
            # Patch already applied - silent return
            _patch_applied = True
            return True
        
        # If force is False and _patch_applied is True, skip (double-check)
        if _patch_applied and not force:
            return True
        
        # Get the original method
        if not hasattr(CommandPathPost, '_write_file'):
            if FreeCAD:
                FreeCAD.Console.PrintError(
                    "WoodWOP Patch: CommandPathPost._write_file method not found\n"
                )
            return False
        
        # Store original method if not already stored
        if _original_write_file is None:
            _original_write_file = CommandPathPost._write_file
        
        # Create patched method
        patched_method = _create_patched_method(_original_write_file)
        
        # Replace the method
        CommandPathPost._write_file = patched_method
        
        _patch_applied = True
        
        # Only print message on first application
        if FreeCAD:
            FreeCAD.Console.PrintMessage(
                "WoodWOP Patch: Applied patch to Command.py _write_file method\n"
            )
        
        return True
    except Exception as e:
        if FreeCAD:
            FreeCAD.Console.PrintError(
                f"WoodWOP Patch: Failed to apply patch to Command.py: {e}\n"
            )
            import traceback
            FreeCAD.Console.PrintError(f"Traceback: {traceback.format_exc()}\n")
        return False


def remove_patch():
    """
    Remove the monkey patch (if needed for testing).
    
    Returns:
        bool: True if patch was removed successfully, False otherwise
    """
    global _patch_applied, _original_write_file
    
    if not _import_freecad_modules():
        return False
    
    if CommandPathPost is None or _original_write_file is None:
        return False
    
    try:
        if hasattr(CommandPathPost, '_write_file') and \
           hasattr(CommandPathPost._write_file, '_woodwop_patched'):
            # Restore original method
            CommandPathPost._write_file = _original_write_file
            _patch_applied = False
            if FreeCAD:
                FreeCAD.Console.PrintMessage(
                    "WoodWOP Patch: Removed patch from Command.py\n"
                )
            return True
        return False
    except Exception as e:
        if FreeCAD:
            FreeCAD.Console.PrintError(
                f"WoodWOP Patch: Failed to remove patch: {e}\n"
            )
        return False


def ensure_patch_applied():
    """
    Ensure patch is applied. This is a convenience function that can be called
    multiple times safely. It will apply the patch if it's not already applied.
    
    This function is called automatically when needed, but can also be called
    manually for extra safety.
    
    Returns:
        bool: True if patch is applied (or was already applied), False otherwise
    """
    global _patch_applied
    if _patch_applied:
        # Double-check that patch is still in place
        if _import_freecad_modules() and CommandPathPost is not None:
            if hasattr(CommandPathPost, '_write_file') and \
               hasattr(CommandPathPost._write_file, '_woodwop_patched'):
                return True
            else:
                # Patch was removed somehow, reapply
                _patch_applied = False
                return apply_patch(force=True)
        return True
    
    return apply_patch()


# Auto-apply patch when module is imported (if FreeCAD is available)
# This ensures the patch is applied as early as possible
if _import_freecad_modules():
    apply_patch()
