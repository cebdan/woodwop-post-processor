"""
Configuration module for WoodWOP Post Processor.
Contains all global variables, constants, and configuration settings.
"""

import datetime

# Tooltips for FreeCAD UI
TOOLTIP = '''
WoodWOP MPR post processor for HOMAG CNC machines.
Converts FreeCAD Path operations to WoodWOP MPR 4.0 format.

The .nc file will be AUTOMATICALLY renamed to .mpr after export!
The .mpr file will be ready almost instantly.

If auto-rename fails, manually rename .nc to .mpr
'''

TOOLTIP_ARGS = '''
--no-comments: Suppress comment output
--precision=X: Set coordinate precision (default 3)
--workpiece-length=X: Workpiece length in mm (default: auto-detect)
--workpiece-width=Y: Workpiece width in mm (default: auto-detect)
--workpiece-thickness=Z: Workpiece thickness in mm (default: auto-detect)
--use-part-name: Name .mpr file after the part/body name instead of document name
--g54: Set coordinate system offset to minimum part coordinates (legacy flag)
  When set, MPR coordinates will be offset by minimum part coordinates (X, Y, Z).
  Origin (0,0,0) will be at the minimum point of the part.
  NOTE: G-code output is NOT affected and remains unchanged.
  PREFERRED: Use Work Coordinate Systems (Fixtures) in Job settings instead of this flag.
  If G54 is checked in Job settings, it will automatically be used.
--log or /log: Enable verbose logging (detailed debug output)
  When set, detailed debug information will be printed to console and log file.
  If not set, only critical errors and warnings are shown.
--report or /report: Enable job report generation
  When set, a detailed job report file (_job_report.txt) will be created.
  If not set, no report file will be generated.
--nc or /nc: Enable NC (G-code) file output
  When set, both MPR and NC files will be created.
  If not set, only MPR file will be created.
--p_c or /p_c or --p-c or /p-c: Enable Path Commands export
  When set, a detailed path commands file (_path_commands.txt) will be created.
  The file contains all Path Commands from all operations for debugging and analysis.
  If not set, no path commands file will be generated.
--use_g0 or /use_g0: Enable G0 processing as G1 (linear moves)
  
  LOGIC:
  - If flag is SET: ALL G0 commands are processed as G1 (linear moves) and added to contour
  - If flag is NOT SET (default): G0 chains at start and end of trajectory are SKIPPED:
    * G0 commands before first working element (G1/G2/G3) are skipped (only position updated)
    * G0 commands after last working element (G1/G2/G3) are skipped (only position updated)
    * G0 commands BETWEEN working elements are still processed as G1 (part of contour)
  
  This is useful because FreeCAD generates approach/retract moves (G0) that should not be
  included in the contour, as WoodWOP handles these automatically.
  
  Example:
    Commands: [G0, G0, G1, G0, G2, G0, G0]
    - Without flag: G0 at start/end skipped, G0 between G1/G2 processed
    - With flag: ALL G0 processed as G1
'''

# File extension for WoodWOP MPR files
POSTPROCESSOR_FILE_NAME = 'woodwop_post'
FILE_EXTENSION = '.mpr'
UNITS = 'G21'  # Metric units

# Current timestamp
now = datetime.datetime.now()

# Post processor configuration
PRECISION = 3
OUTPUT_COMMENTS = True
WORKPIECE_LENGTH = None
WORKPIECE_WIDTH = None
WORKPIECE_THICKNESS = None
STOCK_EXTENT_X = 0.0
STOCK_EXTENT_Y = 0.0
STOCK_EXTENT_X_NEG = 0.0  # l_off (left offset)
STOCK_EXTENT_X_POS = 0.0  # r_oz (right oversize)
STOCK_EXTENT_Y_NEG = 0.0  # f_off (front offset)
STOCK_EXTENT_Y_POS = 0.0  # b_oz (back oversize)
USE_PART_NAME = False

# Program offsets (for workpiece positioning in WoodWOP)
PROGRAM_OFFSET_X = 0.0
PROGRAM_OFFSET_Y = 0.0
PROGRAM_OFFSET_Z = 0.0

# Coordinate system offset (for G54, G55, etc.)
COORDINATE_SYSTEM = None  # None, 'G54', 'G55', 'G56', 'G57', 'G58', 'G59'
COORDINATE_OFFSET_X = 0.0
COORDINATE_OFFSET_Y = 0.0
COORDINATE_OFFSET_Z = 0.0

# Feature flags
ENABLE_VERBOSE_LOGGING = False
ENABLE_JOB_REPORT = False
OUTPUT_NC_FILE = False
ENABLE_PATH_COMMANDS_EXPORT = False
ENABLE_PROCESSING_ANALYSIS = False
ENABLE_NO_Z_SAFE20 = False
USE_G0 = False  # If False: G0 chains at start/end of trajectory are skipped
ENABLE_G0_START = False  # If True: Add G0 rapid move to start of contours
USE_Z_PART = False  # If True: Use Z coordinates from Job without correction

# G0 tracking for /g0_start feature
LAST_G0_POSITION = None  # (x, y, z) tuple of last G0 position before first G1/G2/G3

# Tracking state
contour_counter = 1
contours = []
operations = []
tools_used = set()



