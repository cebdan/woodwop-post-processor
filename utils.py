"""
Utility functions for WoodWOP Post Processor.
Contains helper functions for formatting, logging, etc.
"""

from . import config


def debug_log(message):
    """Print debug message only if verbose logging is enabled."""
    if config.ENABLE_VERBOSE_LOGGING:
        print(message)
        try:
            import FreeCAD
            FreeCAD.Console.PrintMessage(message + "\n")
        except:
            pass


def fmt(value):
    """Format numeric value with precision."""
    return f"{value:.{config.PRECISION}f}"


def linenumber():
    """Not used in MPR format."""
    return ''



