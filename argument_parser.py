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
    
    if not argstring:
        return {}
    
    print(f"[WoodWOP] Parsing arguments: '{argstring}'")
    args = argstring.split()
    print(f"[WoodWOP] Split into {len(args)} arguments: {args}")
    
    for arg in args:
        # Normalize argument to handle both -- and / formats
        normalized_arg = arg.lstrip('-').lstrip('/')
        print(f"[WoodWOP] Processing argument: '{arg}' (normalized: '{normalized_arg}')")
        
        if arg == '--log' or normalized_arg == 'log':
            config.ENABLE_VERBOSE_LOGGING = True
            print(f"[WoodWOP] Verbose logging enabled via {arg} flag")
            _update_module_flag('ENABLE_VERBOSE_LOGGING', True)
            
        elif arg == '--report' or normalized_arg == 'report':
            config.ENABLE_JOB_REPORT = True
            print(f"[WoodWOP] Job report generation enabled via {arg} flag")
            _update_module_flag('ENABLE_JOB_REPORT', True)
            
        elif arg in ['--no_z_safe20', '/no_z_safe20'] or normalized_arg == 'no_z_safe20':
            config.ENABLE_NO_Z_SAFE20 = True
            print(f"[WoodWOP] 20mm minimum for z_safe disabled via /no_z_safe20 flag")
            _update_module_flag('ENABLE_NO_Z_SAFE20', True)
            
        elif arg == '--nc' or normalized_arg == 'nc':
            config.OUTPUT_NC_FILE = True
            print(f"[WoodWOP] NC file output enabled via {arg} flag")
            _update_module_flag('OUTPUT_NC_FILE', True)
            
        elif arg in ['--p_c', '--p-c'] or normalized_arg in ['p_c', 'p-c']:
            config.ENABLE_PATH_COMMANDS_EXPORT = True
            print(f"[WoodWOP] Path commands export enabled via {arg} flag")
            _update_module_flag('ENABLE_PATH_COMMANDS_EXPORT', True)
            
        elif arg in ['--use_g0', '/use_g0'] or normalized_arg == 'use_g0':
            config.USE_G0 = True
            print(f"[WoodWOP] G0 processing enabled via {arg} flag (G0 will be treated as G1)")
            _update_module_flag('USE_G0', True)
            
        elif arg in ['--p_a', '--p-a'] or normalized_arg in ['p_a', 'p-a']:
            config.ENABLE_PROCESSING_ANALYSIS = True
            print(f"[WoodWOP] Processing analysis export enabled via {arg} flag")
            _update_module_flag('ENABLE_PROCESSING_ANALYSIS', True)
            
        elif arg == '--no-comments' or normalized_arg == 'no-comments':
            config.OUTPUT_COMMENTS = False
            print(f"[WoodWOP] OUTPUT_COMMENTS = False")
            
        elif arg == '--use-part-name' or normalized_arg == 'use-part-name':
            config.USE_PART_NAME = True
            print(f"[WoodWOP] USE_PART_NAME = True")
            
        elif arg.startswith('--precision=') or normalized_arg.startswith('precision='):
            value = arg.split('=')[1] if '=' in arg else normalized_arg.split('=')[1]
            config.PRECISION = int(value)
            print(f"[WoodWOP] PRECISION = {config.PRECISION}")
            
        elif arg.startswith('--workpiece-length=') or normalized_arg.startswith('workpiece-length='):
            value = arg.split('=')[1] if '=' in arg else normalized_arg.split('=')[1]
            config.WORKPIECE_LENGTH = float(value)
            print(f"[WoodWOP] WORKPIECE_LENGTH = {config.WORKPIECE_LENGTH}")
            
        elif arg.startswith('--workpiece-width=') or normalized_arg.startswith('workpiece-width='):
            value = arg.split('=')[1] if '=' in arg else normalized_arg.split('=')[1]
            config.WORKPIECE_WIDTH = float(value)
            print(f"[WoodWOP] WORKPIECE_WIDTH = {config.WORKPIECE_WIDTH}")
            
        elif arg.startswith('--workpiece-thickness=') or normalized_arg.startswith('workpiece-thickness='):
            value = arg.split('=')[1] if '=' in arg else normalized_arg.split('=')[1]
            config.WORKPIECE_THICKNESS = float(value)
            print(f"[WoodWOP] WORKPIECE_THICKNESS = {config.WORKPIECE_THICKNESS}")
            
        elif arg in ['--g54', '--G54'] or normalized_arg.lower() == 'g54':
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
    
    return {}


def _update_module_flag(flag_name, value):
    """Update flag in current module for FreeCAD compatibility."""
    import sys
    current_module = sys.modules.get(__name__)
    if current_module:
        setattr(current_module, flag_name, value)



