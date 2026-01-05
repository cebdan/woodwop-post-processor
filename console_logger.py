"""
Console logger module for WoodWOP Post Processor.
Handles logging of FreeCAD Console output to file.
"""

import os
from . import config

# Global state for console logging
_console_log_initialized = False
_original_print_message = None
_original_print_warning = None
_original_print_error = None
_original_print_log = None


def _get_log_file_path():
    """Get path to console log file in module root directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, '_freecad_console_log.txt')


def _append_to_log_file(message):
    """
    Append message to console log file.
    
    Args:
        message: Message to append
    """
    if not hasattr(config, 'ENABLE_FREECAD_CONSOLE_LOG') or not config.ENABLE_FREECAD_CONSOLE_LOG:
        return
    
    try:
        log_path = _get_log_file_path()
        # Use append mode for subsequent writes
        with open(log_path, 'a', encoding='utf-8', errors='replace') as f:
            f.write(message)
    except Exception:
        # Silently fail - don't break the main functionality
        pass


def _create_patched_print_method(original_method, level):
    """
    Create a patched version of FreeCAD Console print method.
    
    Args:
        original_method: Original FreeCAD.Console method
        level: Message level ('message', 'warning', 'error', 'log')
        
    Returns:
        function: Patched method that logs to file and calls original
    """
    def patched_method(message):
        """Patched method that logs to file and calls original."""
        # Call original method first
        original_method(message)
        
        # Log to file
        if hasattr(config, 'ENABLE_FREECAD_CONSOLE_LOG') and config.ENABLE_FREECAD_CONSOLE_LOG:
            _append_to_log_file(message)
    
    return patched_method


def initialize_console_logging():
    """
    Initialize FreeCAD Console logging by patching Console methods.
    
    This function patches FreeCAD.Console.PrintMessage, PrintWarning, PrintError
    to also write to a log file when ENABLE_FREECAD_CONSOLE_LOG is True.
    
    File is always cleared (mode 'w') at each call to show only the latest session.
    """
    global _console_log_initialized
    global _original_print_message
    global _original_print_warning
    global _original_print_error
    global _original_print_log
    
    # Check if flag exists and is enabled
    if not hasattr(config, 'ENABLE_FREECAD_CONSOLE_LOG') or not config.ENABLE_FREECAD_CONSOLE_LOG:
        return
    
    try:
        import FreeCAD
        
        # ALWAYS clear log file at start (write mode 'w')
        # This ensures we only see the latest session output
        log_path = _get_log_file_path()
        with open(log_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write("=== FreeCAD Console Log Started ===\n")
            f.write(f"Log file: {log_path}\n")
            f.write("=" * 50 + "\n\n")
        
        # Only patch methods once (to avoid multiple patches)
        if not _console_log_initialized:
            # Store original methods
            if hasattr(FreeCAD.Console, 'PrintMessage'):
                _original_print_message = FreeCAD.Console.PrintMessage
                FreeCAD.Console.PrintMessage = _create_patched_print_method(
                    _original_print_message, 'message'
                )
            
            if hasattr(FreeCAD.Console, 'PrintWarning'):
                _original_print_warning = FreeCAD.Console.PrintWarning
                FreeCAD.Console.PrintWarning = _create_patched_print_method(
                    _original_print_warning, 'warning'
                )
            
            if hasattr(FreeCAD.Console, 'PrintError'):
                _original_print_error = FreeCAD.Console.PrintError
                FreeCAD.Console.PrintError = _create_patched_print_method(
                    _original_print_error, 'error'
                )
            
            if hasattr(FreeCAD.Console, 'PrintLog'):
                _original_print_log = FreeCAD.Console.PrintLog
                FreeCAD.Console.PrintLog = _create_patched_print_method(
                    _original_print_log, 'log'
                )
            
            _console_log_initialized = True
        
        # Log initialization message (this will also be written to file)
        if FreeCAD:
            FreeCAD.Console.PrintMessage(
                f"[WoodWOP] Console logging initialized: {log_path}\n"
            )
    except ImportError:
        # FreeCAD not available - this is OK
        pass
    except Exception as e:
        # Silently fail - don't break the main functionality
        pass


def cleanup_console_logging():
    """
    Restore original FreeCAD Console methods.
    
    This function restores the original Console methods if they were patched.
    """
    global _console_log_initialized
    global _original_print_message
    global _original_print_warning
    global _original_print_error
    global _original_print_log
    
    if not _console_log_initialized:
        return
    
    try:
        import FreeCAD
        
        if _original_print_message is not None:
            FreeCAD.Console.PrintMessage = _original_print_message
        if _original_print_warning is not None:
            FreeCAD.Console.PrintWarning = _original_print_warning
        if _original_print_error is not None:
            FreeCAD.Console.PrintError = _original_print_error
        if _original_print_log is not None:
            FreeCAD.Console.PrintLog = _original_print_log
        
        _console_log_initialized = False
    except ImportError:
        pass
    except Exception:
        pass
