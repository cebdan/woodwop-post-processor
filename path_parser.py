"""
Path parser module for WoodWOP Post Processor.
Handles extraction of contours and operations from FreeCAD Path commands.
"""

import math
from . import config
from . import utils

# Try to import FreeCAD Path utilities
try:
    import PathScripts.PathUtils as PathUtils
except ImportError:
    PathUtils = None


def extract_contour_from_path(obj):
    """
    Extract contour elements (points, lines, arcs) from Path commands.
    
    Args:
        obj: FreeCAD Path object
        
    Returns:
        tuple: (elements, start_pos) where elements is a list of contour elements
               and start_pos is (x, y, z) tuple
    """
    # Log USE_G0 flag value at start of extraction
    utils.debug_log(f"[WoodWOP DEBUG] extract_contour_from_path(): USE_G0 = {config.USE_G0}")
    
    elements = []
    current_x = 0.0
    current_y = 0.0
    current_z = 0.0
    start_x = None
    start_y = None
    start_z = None

    if not hasattr(obj, 'Path'):
        return elements, (0.0, 0.0, 0.0)

    # Use PathUtils.getPathWithPlacement to get commands with placement transformation
    if PathUtils is None:
        path_commands = obj.Path.Commands if hasattr(obj.Path, 'Commands') else []
    else:
        try:
            path_commands = PathUtils.getPathWithPlacement(obj).Commands
        except:
            path_commands = obj.Path.Commands if hasattr(obj.Path, 'Commands') else []
    
    if not path_commands:
        return elements, (0.0, 0.0, 0.0)

    # If USE_G0 is False, find first and last "working" elements (G1/G2/G3)
    # G0 chains before first and after last working elements will be skipped
    first_working_idx = None
    last_working_idx = None
    
    if not config.USE_G0:
        # First pass: find indices of first and last working elements
        for idx, cmd in enumerate(path_commands):
            if cmd.Name in ['G1', 'G01', 'G2', 'G02', 'G3', 'G03']:
                if first_working_idx is None:
                    first_working_idx = idx
                last_working_idx = idx
        utils.debug_log(f"[WoodWOP DEBUG] USE_G0=False: first_working_idx={first_working_idx}, last_working_idx={last_working_idx}")
    else:
        utils.debug_log(f"[WoodWOP DEBUG] USE_G0=True: All G0 commands will be processed as G1 (linear moves)")

    # Second pass: process commands
    for idx, cmd in enumerate(path_commands):
        params = cmd.Parameters

        # Update position
        x = params.get('X', current_x)
        y = params.get('Y', current_y)
        z = params.get('Z', current_z)

        # Save start position from first movement command
        if start_x is None and cmd.Name in ['G0', 'G00', 'G1', 'G01', 'G2', 'G02', 'G3', 'G03']:
            start_x = current_x
            start_y = current_y
            start_z = current_z

        # G0 (rapid move) processing
        if cmd.Name in ['G0', 'G00']:
            # Check if there is actual movement (dX, dY, or dZ)
            dx = abs(x - current_x)
            dy = abs(y - current_y)
            dz = abs(z - current_z)
            
            # Skip zero movements
            if dx < 0.001 and dy < 0.001 and dz < 0.001:
                # Update position only (no element added)
                current_x = x
                current_y = y
                current_z = z
                continue
            
            # CRITICAL: If USE_G0 is True, process ALL G0 as G1 (linear moves)
            if config.USE_G0:
                utils.debug_log(f"[WoodWOP DEBUG] USE_G0=True: Processing G0 at index {idx} as G1 (linear move)")
                # Process G0 as G1 (linear move) - create line element
                line_elem = {
                    'type': 'KL',  # Line
                    'x': x,
                    'y': y,
                    'z': z,  # Always include Z coordinate
                    'move_type': 'G0'  # Store original movement type for analysis
                }
                elements.append(line_elem)
                current_x = x
                current_y = y
                current_z = z
                continue  # Skip rest of G0 processing logic
            
            # If USE_G0 is False, skip G0 chains at start/end of trajectory
            # But only if there are working elements (G1/G2/G3)
            # If there are no working elements, process all G0 as G1
            if first_working_idx is not None or last_working_idx is not None:
                # There are working elements - skip G0 at start/end
                # Skip G0 before first working element
                if first_working_idx is not None and idx < first_working_idx:
                    utils.debug_log(f"[WoodWOP DEBUG] USE_G0=False: Skipping G0 at index {idx} (before first working element)")
                    # Update position only (no element added)
                    current_x = x
                    current_y = y
                    current_z = z
                    continue
                # Skip G0 after last working element
                if last_working_idx is not None and idx > last_working_idx:
                    utils.debug_log(f"[WoodWOP DEBUG] USE_G0=False: Skipping G0 at index {idx} (after last working element)")
                    # Update position only (no element added)
                    current_x = x
                    current_y = y
                    current_z = z
                    continue
                # G0 is between working elements - process as G1
                utils.debug_log(f"[WoodWOP DEBUG] USE_G0=False: Processing G0 at index {idx} as G1 (between working elements)")
            else:
                # No working elements - process all G0 as G1
                utils.debug_log(f"[WoodWOP DEBUG] USE_G0=False: Processing G0 at index {idx} as G1 (no working elements found)")
            line_elem = {
                'type': 'KL',  # Line
                'x': x,
                'y': y,
                'z': z,  # Always include Z coordinate
                'move_type': 'G0'  # Store original movement type for analysis
            }
            elements.append(line_elem)
            current_x = x
            current_y = y
            current_z = z

        # Linear move (G1) - create line
        elif cmd.Name in ['G1', 'G01']:
            # Check if there is actual movement (dX, dY, or dZ)
            # Skip if all movements are less than 0.001 (no actual movement)
            dx = abs(x - current_x)
            dy = abs(y - current_y)
            dz = abs(z - current_z)
            if not (dx < 0.001 and dy < 0.001 and dz < 0.001):
                line_elem = {
                    'type': 'KL',  # Line
                    'x': x,
                    'y': y,
                    'z': z,  # Always include Z coordinate
                    'move_type': 'G1'  # Store original movement type for analysis
                }
                elements.append(line_elem)
            current_x = x
            current_y = y
            current_z = z

        # Arc move (G2, G3) - create arc
        elif cmd.Name in ['G2', 'G02', 'G3', 'G03']:
            i = params.get('I', 0)
            j = params.get('J', 0)
            direction = 'CW' if cmd.Name in ['G2', 'G02'] else 'CCW'

            # WoodWOP limitation: arcs do not support Z-axis changes
            # If Z changes during arc, we must convert to line segments
            z_changes = abs(z - current_z) > 0.001

            if z_changes:
                # Convert arc with Z change to line segments
                # Calculate center point
                center_x = current_x + i
                center_y = current_y + j
                radius = math.sqrt(i*i + j*j) if (i != 0 or j != 0) else 0

                # Discretize arc into line segments
                # Calculate start and end angles
                start_angle = math.atan2(current_y - center_y, current_x - center_x)
                end_angle = math.atan2(y - center_y, x - center_x)

                # Normalize angles
                if direction == 'CCW' and end_angle < start_angle:
                    end_angle += 2 * math.pi
                elif direction == 'CW' and end_angle > start_angle:
                    end_angle -= 2 * math.pi

                # Number of segments (more segments = smoother curve)
                num_segments = max(8, int(abs(end_angle - start_angle) * 180 / math.pi / 5))  # ~5 degrees per segment

                for seg in range(1, num_segments + 1):
                    t = seg / num_segments
                    angle = start_angle + (end_angle - start_angle) * t
                    seg_x = center_x + radius * math.cos(angle)
                    seg_y = center_y + radius * math.sin(angle)
                    seg_z = current_z + (z - current_z) * t

                    line_elem = {
                        'type': 'KL',  # Line
                        'x': seg_x,
                        'y': seg_y,
                        'z': seg_z
                    }
                    elements.append(line_elem)
                # Update position after arc with Z change (converted to segments)
                current_x = x
                current_y = y
                current_z = z
            else:
                # Normal arc in XY plane - no Z change
                # Calculate center point (I, J are offsets from start point)
                center_x = current_x + i
                center_y = current_y + j
                radius = math.sqrt(i*i + j*j) if (i != 0 or j != 0) else 0

                # Calculate intermediate point for three-point arc format (X2, Y2)
                # Use midpoint of arc as intermediate point
                start_angle = math.atan2(current_y - center_y, current_x - center_x)
                end_angle = math.atan2(y - center_y, x - center_x)
                
                # Normalize angles for direction
                if direction == 'CCW' and end_angle < start_angle:
                    end_angle += 2 * math.pi
                elif direction == 'CW' and end_angle > start_angle:
                    end_angle -= 2 * math.pi
                
                mid_angle = (start_angle + end_angle) / 2
                mid_x = center_x + radius * math.cos(mid_angle)
                mid_y = center_y + radius * math.sin(mid_angle)

                arc_elem = {
                    'type': 'KA',  # Arc
                    'x': x,  # End point X
                    'y': y,  # End point Y
                    'i': i,  # Center offset in X (from start point)
                    'j': j,  # Center offset in Y (from start point)
                    'x2': mid_x,  # Intermediate point X (for three-point format)
                    'y2': mid_y,  # Intermediate point Y (for three-point format)
                    'r': radius,
                    'direction': direction,
                    'z': z  # Always include Z coordinate
                }
                elements.append(arc_elem)

        current_x = x
        current_y = y
        current_z = z

    # Return elements and start position
    start_pos = (start_x if start_x is not None else 0.0,
                 start_y if start_y is not None else 0.0,
                 start_z if start_z is not None else 0.0)
    return elements, start_pos


def extract_drilling_operations(obj, get_tool_number_func):
    """
    Extract drilling positions from Path object.
    
    Args:
        obj: FreeCAD Path object
        get_tool_number_func: Function to get tool number from object
        
    Returns:
        list: List of drilling operations
    """
    drilling_ops = []
    tool_number = get_tool_number_func(obj) if get_tool_number_func else None

    if not hasattr(obj, 'Path'):
        return drilling_ops

    # Use PathUtils.getPathWithPlacement to get commands with placement transformation
    if PathUtils is None:
        path_commands = obj.Path.Commands if hasattr(obj.Path, 'Commands') else []
    else:
        try:
            path_commands = PathUtils.getPathWithPlacement(obj).Commands
        except:
            path_commands = obj.Path.Commands if hasattr(obj.Path, 'Commands') else []

    if not path_commands:
        return drilling_ops

    # Collect drilling positions
    drill_positions = []
    current_x = 0.0
    current_y = 0.0
    current_z = 0.0
    depth = 10.0

    for cmd in path_commands:
        params = cmd.Parameters

        if cmd.Name in ['G81', 'G82', 'G83']:  # Drilling cycles
            x = params.get('X', current_x)
            y = params.get('Y', current_y)
            z = params.get('Z', current_z)
            r = params.get('R', 0)  # Retract height

            drill_depth = abs(z - r) if r != 0 else abs(z)

            drill_positions.append({
                'x': x,
                'y': y,
                'depth': drill_depth
            })

            current_x = x
            current_y = y
            depth = drill_depth

        elif cmd.Name in ['G0', 'G00', 'G1', 'G01']:
            current_x = params.get('X', current_x)
            current_y = params.get('Y', current_y)
            current_z = params.get('Z', current_z)

    # Create BohrVert (vertical drilling) operation for each position
    for pos in drill_positions:
        drilling_ops.append({
            'type': 'BohrVert',
            'id': 102,
            'xa': pos['x'],
            'ya': pos['y'],
            'depth': pos['depth'],
            'tool': tool_number
        })

    return drilling_ops

