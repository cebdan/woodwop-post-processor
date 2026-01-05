"""
Argument parser module for WoodWOP Post Processor.
Handles parsing of command-line arguments and setting configuration flags.
"""

from . import config
from . import utils


def parse_arguments(argstring):
    """
    Parse command-line arguments and update configuration.
    
    Args:
        argstring: String containing command-line arguments
        
    Returns:
        dict: Parsed arguments and flags
    """
    # Reset flags first
    config.ENABLE_VERBOSE_LOGGING = False
    config.ENABLE_JOB_REPORT = False
    config.OUTPUT_NC_FILE = False
    config.ENABLE_PATH_COMMANDS_EXPORT = False
    config.ENABLE_PROCESSING_ANALYSIS = False
    config.ENABLE_NO_Z_SAFE20 = False
    config.USE_G0 = False
    config.USE_Z_PART = False
    
    if not argstring:
        return {}
    
    print(f"[WoodWOP] Parsing arguments: '{argstring}'")
    args = argstring.split()
    print(f"[WoodWOP] Split into {len(args)} arguments: {args}")
    
    for arg in args:
        # Only support slash format (/flag), not double-dash (--flag)
        if not arg.startswith('/'):
            print(f"[WoodWOP WARNING] Argument '{arg}' ignored - only slash format (/flag) is supported")
            continue
        
        # Normalize argument (remove leading slash)
        normalized_arg = arg.lstrip('/')
        print(f"[WoodWOP] Processing argument: '{arg}' (normalized: '{normalized_arg}')")
        
        if normalized_arg == 'log':
            config.ENABLE_VERBOSE_LOGGING = True
            print(f"[WoodWOP] Verbose logging enabled via {arg} flag")
            _update_module_flag('ENABLE_VERBOSE_LOGGING', True)
            
        elif normalized_arg == 'report':
            config.ENABLE_JOB_REPORT = True
            print(f"[WoodWOP] Job report generation enabled via {arg} flag")
            _update_module_flag('ENABLE_JOB_REPORT', True)
            
        elif normalized_arg == 'no_z_safe20':
            config.ENABLE_NO_Z_SAFE20 = True
            print(f"[WoodWOP] 20mm minimum for z_safe disabled via {arg} flag")
            _update_module_flag('ENABLE_NO_Z_SAFE20', True)
            
        elif normalized_arg == 'nc':
            config.OUTPUT_NC_FILE = True
            print(f"[WoodWOP] NC file output enabled via {arg} flag")
            _update_module_flag('OUTPUT_NC_FILE', True)
            
        elif normalized_arg in ['p_c', 'p-c']:
            config.ENABLE_PATH_COMMANDS_EXPORT = True
            print(f"[WoodWOP] Path commands export enabled via {arg} flag")
            _update_module_flag('ENABLE_PATH_COMMANDS_EXPORT', True)
            
        elif normalized_arg == 'use_g0':
            config.USE_G0 = True
            print(f"[WoodWOP] G0 processing enabled via {arg} flag (G0 will be treated as G1)")
            _update_module_flag('USE_G0', True)
            
        elif normalized_arg == 'f_con':
            config.ENABLE_FREECAD_CONSOLE_LOG = True
            print(f"[WoodWOP] FreeCAD Console logging enabled via {arg} flag")
            _update_module_flag('ENABLE_FREECAD_CONSOLE_LOG', True)
            
        elif normalized_arg in ['p_a', 'p-a']:
            config.ENABLE_PROCESSING_ANALYSIS = True
            print(f"[WoodWOP] Processing analysis export enabled via {arg} flag")
            _update_module_flag('ENABLE_PROCESSING_ANALYSIS', True)
            
        elif normalized_arg == 'no-comments':
            config.OUTPUT_COMMENTS = False
            print("[WoodWOP] OUTPUT_COMMENTS = False")
            
        elif normalized_arg == 'use-part-name':
            config.USE_PART_NAME = True
            print("[WoodWOP] USE_PART_NAME = True")
            
        elif normalized_arg.startswith('precision='):
            value = normalized_arg.split('=')[1]
            try:
                precision_value = int(value)
                if precision_value < 1 or precision_value > 6:
                    print(f"[WoodWOP WARNING] Invalid precision: {precision_value}, must be between 1 and 6. Using 3.")
                    precision_value = 3
                config.PRECISION = precision_value
                print(f"[WoodWOP] PRECISION = {precision_value}")
            except ValueError:
                print(f"[WoodWOP WARNING] Invalid precision value: '{value}', must be an integer. Using 3.")
                config.PRECISION = 3
            
        elif normalized_arg.startswith('workpiece-length='):
            value = normalized_arg.split('=')[1]
            try:
                length_value = float(value)
                if length_value <= 0:
                    print(f"[WoodWOP WARNING] Invalid workpiece length: {length_value}, must be positive. Ignoring.")
                else:
                    config.WORKPIECE_LENGTH = length_value
                    print(f"[WoodWOP] WORKPIECE_LENGTH = {config.WORKPIECE_LENGTH}")
            except ValueError:
                print(f"[WoodWOP WARNING] Invalid workpiece length value: '{value}', must be a number. Ignoring.")
            
        elif normalized_arg.startswith('workpiece-width='):
            value = normalized_arg.split('=')[1]
            try:
                width_value = float(value)
                if width_value <= 0:
                    print(f"[WoodWOP WARNING] Invalid workpiece width: {width_value}, must be positive. Ignoring.")
                else:
                    config.WORKPIECE_WIDTH = width_value
                    print(f"[WoodWOP] WORKPIECE_WIDTH = {config.WORKPIECE_WIDTH}")
            except ValueError:
                print(f"[WoodWOP WARNING] Invalid workpiece width value: '{value}', must be a number. Ignoring.")
            
        elif normalized_arg.startswith('workpiece-thickness='):
            value = normalized_arg.split('=')[1]
            try:
                thickness_value = float(value)
                if thickness_value <= 0:
                    print(f"[WoodWOP WARNING] Invalid workpiece thickness: {thickness_value}, must be positive. Ignoring.")
                else:
                    config.WORKPIECE_THICKNESS = thickness_value
                    print(f"[WoodWOP] WORKPIECE_THICKNESS = {config.WORKPIECE_THICKNESS}")
            except ValueError:
                print(f"[WoodWOP WARNING] Invalid workpiece thickness value: '{value}', must be a number. Ignoring.")
            
        elif normalized_arg in ['z_part', 'z-part']:
            config.USE_Z_PART = True
            print(f"[WoodWOP] Z coordinates from Job without offset correction enabled via {arg} flag")
            _update_module_flag('USE_Z_PART', True)
            
        elif normalized_arg.lower() == 'g54':
            # Legacy flag support - will be overridden by Job.Fixtures if present
            config.COORDINATE_SYSTEM = 'G54'
            print(f"[WoodWOP] COORDINATE_SYSTEM = G54 (via {arg} flag)")
            utils.debug_log(f"[WoodWOP DEBUG] Coordinate system set to G54 via {arg} flag (legacy mode)")
    
    # Debug: Print final flag values
    print(f"[WoodWOP] Final flag values after parsing:")
    print(f"[WoodWOP]   OUTPUT_NC_FILE = {config.OUTPUT_NC_FILE}")
    print(f"[WoodWOP]   ENABLE_VERBOSE_LOGGING = {config.ENABLE_VERBOSE_LOGGING}")
    print(f"[WoodWOP]   ENABLE_JOB_REPORT = {config.ENABLE_JOB_REPORT}")
    print(f"[WoodWOP]   ENABLE_PATH_COMMANDS_EXPORT = {config.ENABLE_PATH_COMMANDS_EXPORT}")
    print(f"[WoodWOP]   ENABLE_FREECAD_CONSOLE_LOG = {config.ENABLE_FREECAD_CONSOLE_LOG}")
    print(f"[WoodWOP]   USE_G0 = {config.USE_G0}")
    print(f"[WoodWOP]   USE_Z_PART = {config.USE_Z_PART}")
    
    return {}


def _update_module_flag(flag_name, value):
    """Update flag in current module and config module for FreeCAD compatibility."""
    import sys
    # Update in current module (argument_parser)
    current_module = sys.modules.get(__name__)
    if current_module:
        setattr(current_module, flag_name, value)
    
    # Also update in config module to ensure consistency
    config_module = sys.modules.get('woodwop.config')
    if config_module:
        setattr(config_module, flag_name, value)
    # Also try relative import path
    config_module = sys.modules.get(config.__name__)
    if config_module:
        setattr(config_module, flag_name, value)



