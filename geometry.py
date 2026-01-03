"""
Geometry module for WoodWOP Post Processor.
Handles geometric calculations: bounds, minimums, tool compensation, etc.
"""

from . import config


def calculate_part_minimum():
    """
    Calculate minimum X, Y, Z coordinates from all contours and operations.
    
    This finds the minimum point (intersection of minimum X, Y, Z) which will be used
    as the origin (0,0,0) when G54 or other coordinate system flags are set.
    
    Returns:
        tuple: (min_x, min_y, min_z) or (0.0, 0.0, 0.0) if no coordinates found
    """
    min_x = None
    min_y = None
    min_z = None
    points_checked = 0
    
    # Check all contour elements
    for contour_idx, contour in enumerate(config.contours):
        # Check start position
        start_x, start_y, start_z = contour.get('start_pos', (0.0, 0.0, 0.0))
        if min_x is None or start_x < min_x:
            min_x = start_x
        if min_y is None or start_y < min_y:
            min_y = start_y
        if min_z is None or start_z < min_z:
            min_z = start_z
        points_checked += 1
        
        # Track previous point for arc center calculation
        prev_x = start_x
        prev_y = start_y
        prev_z = start_z
        
        # Check all elements in contour
        for elem_idx, elem in enumerate(contour.get('elements', [])):
            x = elem.get('x', 0.0)
            y = elem.get('y', 0.0)
            z = elem.get('z', 0.0)
            
            # Check end point
            if min_x is None or x < min_x:
                min_x = x
            if min_y is None or y < min_y:
                min_y = y
            if min_z is None or z < min_z:
                min_z = z
            points_checked += 1
            
            # For arcs, also check center point (I, J are relative to previous point)
            if elem.get('type') == 'KA':  # Arc element
                center_x = prev_x + elem.get('i', 0.0)
                center_y = prev_y + elem.get('j', 0.0)
                center_z = prev_z  # Arc center Z is same as previous Z for XY plane arcs
                
                # Check center point
                if min_x is None or center_x < min_x:
                    min_x = center_x
                if min_y is None or center_y < min_y:
                    min_y = center_y
                if min_z is None or center_z < min_z:
                    min_z = center_z
                points_checked += 1
                
                # For arcs, also check if radius extends beyond end point
                # Calculate arc extent (center ± radius)
                radius = elem.get('r', 0.0)
                if radius > 0.001:
                    # Check X extent
                    arc_min_x = center_x - radius
                    arc_min_y = center_y - radius
                    if min_x is None or arc_min_x < min_x:
                        min_x = arc_min_x
                    if min_y is None or arc_min_y < min_y:
                        min_y = arc_min_y
            
            # Update previous point for next iteration
            prev_x = x
            prev_y = y
            prev_z = z
    
    # Check all drilling operations
    for op in config.operations:
        if op.get('type') == 'BohrVert':
            xa = op.get('xa', 0.0)
            ya = op.get('ya', 0.0)
            # Z is typically at surface (0) for drilling, but check depth
            depth = op.get('depth', 0.0)
            z = -depth  # Depth is negative Z
            
            if min_x is None or xa < min_x:
                min_x = xa
            if min_y is None or ya < min_y:
                min_y = ya
            if min_z is None or z < min_z:
                min_z = z
            points_checked += 1
    
    # Log calculation details
    print(f"[WoodWOP DEBUG] calculate_part_minimum(): checked {points_checked} points")
    print(f"[WoodWOP DEBUG]   Contours: {len(config.contours)}, Operations: {len(config.operations)}")
    
    # Return minimum coordinates or (0,0,0) if nothing found
    if min_x is None:
        print(f"[WoodWOP DEBUG]   No coordinates found, returning (0.0, 0.0, 0.0)")
        return (0.0, 0.0, 0.0)
    
    print(f"[WoodWOP DEBUG]   Minimum found: X={min_x:.3f}, Y={min_y:.3f}, Z={min_z:.3f}")
    return (min_x, min_y, min_z)


def calculate_part_bounds():
    """
    Calculate minimum and maximum X, Y, Z coordinates from all contours and operations.
    
    Returns:
        tuple: (min_x, min_y, min_z, max_x, max_y, max_z) or (0.0, 0.0, 0.0, 0.0, 0.0, 0.0) if nothing found
    """
    min_x = None
    min_y = None
    min_z = None
    max_x = None
    max_y = None
    max_z = None
    points_checked = 0
    
    # Check all contour elements
    for contour_idx, contour in enumerate(config.contours):
        # Check start position
        start_x, start_y, start_z = contour.get('start_pos', (0.0, 0.0, 0.0))
        if min_x is None or start_x < min_x:
            min_x = start_x
        if max_x is None or start_x > max_x:
            max_x = start_x
        if min_y is None or start_y < min_y:
            min_y = start_y
        if max_y is None or start_y > max_y:
            max_y = start_y
        if min_z is None or start_z < min_z:
            min_z = start_z
        if max_z is None or start_z > max_z:
            max_z = start_z
        points_checked += 1
        
        # Track previous point for arc center calculation
        prev_x = start_x
        prev_y = start_y
        prev_z = start_z
        
        # Check all elements in contour
        for elem_idx, elem in enumerate(contour.get('elements', [])):
            x = elem.get('x', 0.0)
            y = elem.get('y', 0.0)
            z = elem.get('z', 0.0)
            
            # Check end point
            if min_x is None or x < min_x:
                min_x = x
            if max_x is None or x > max_x:
                max_x = x
            if min_y is None or y < min_y:
                min_y = y
            if max_y is None or y > max_y:
                max_y = y
            if min_z is None or z < min_z:
                min_z = z
            if max_z is None or z > max_z:
                max_z = z
            points_checked += 1
            
            # For arcs, also check center point and arc extent
            if elem.get('type') == 'KA':  # Arc element
                center_x = prev_x + elem.get('i', 0.0)
                center_y = prev_y + elem.get('j', 0.0)
                center_z = prev_z  # Arc center Z is same as previous Z for XY plane arcs
                
                # Check center point
                if min_x is None or center_x < min_x:
                    min_x = center_x
                if max_x is None or center_x > max_x:
                    max_x = center_x
                if min_y is None or center_y < min_y:
                    min_y = center_y
                if max_y is None or center_y > max_y:
                    max_y = center_y
                if min_z is None or center_z < min_z:
                    min_z = center_z
                if max_z is None or center_z > max_z:
                    max_z = center_z
                points_checked += 1
                
                # For arcs, also check if radius extends beyond end point
                # Calculate arc extent (center ± radius)
                radius = elem.get('r', 0.0)
                if radius > 0.001:
                    # Check X and Y extents
                    arc_min_x = center_x - radius
                    arc_max_x = center_x + radius
                    arc_min_y = center_y - radius
                    arc_max_y = center_y + radius
                    if min_x is None or arc_min_x < min_x:
                        min_x = arc_min_x
                    if max_x is None or arc_max_x > max_x:
                        max_x = arc_max_x
                    if min_y is None or arc_min_y < min_y:
                        min_y = arc_min_y
                    if max_y is None or arc_max_y > max_y:
                        max_y = arc_max_y
            
            # Update previous point for next iteration
            prev_x = x
            prev_y = y
            prev_z = z
    
    # Check all drilling operations
    for op in config.operations:
        if op.get('type') == 'BohrVert':
            xa = op.get('xa', 0.0)
            ya = op.get('ya', 0.0)
            # Z is typically at surface (0) for drilling, but check depth
            depth = op.get('depth', 0.0)
            z = -depth  # Depth is negative Z
            
            if min_x is None or xa < min_x:
                min_x = xa
            if max_x is None or xa > max_x:
                max_x = xa
            if min_y is None or ya < min_y:
                min_y = ya
            if max_y is None or ya > max_y:
                max_y = ya
            if min_z is None or z < min_z:
                min_z = z
            if max_z is None or z > max_z:
                max_z = z
            points_checked += 1
    
    # Return bounds or (0,0,0,0,0,0) if nothing found
    if min_x is None:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    return (min_x, min_y, min_z, max_x, max_y, max_z)


def determine_tool_compensation(contour_id):
    """
    Determine tool compensation (RK) based on contour position relative to workpiece.
    
    RK values:
    - "WRKL" - Reference left of workpiece (contour is to the left)
    - "NoWRK" - No workpiece reference (contour is centered/inside)
    - "WRKR" - Reference right of workpiece (contour is to the right)
    
    Args:
        contour_id: ID of the contour
        
    Returns:
        str: RK value ("WRKL", "NoWRK", or "WRKR")
    """
    # Find contour by ID
    contour = None
    for c in config.contours:
        if c['id'] == contour_id:
            contour = c
            break
    
    if not contour or not contour['elements']:
        # Default to NoWRK if contour not found
        return "NoWRK"
    
    # Calculate average X position of contour elements
    x_positions = []
    for elem in contour['elements']:
        if elem['type'] == 'KL':  # Line
            x_positions.append(elem['x'])
        elif elem['type'] == 'KA':  # Arc
            x_positions.append(elem['x'])
        elif elem['type'] == 'KP':  # Point
            x_positions.append(elem['x'])
    
    if not x_positions:
        return "NoWRK"
    
    # Calculate average X position (with coordinate offset applied)
    avg_x = sum(x_positions) / len(x_positions)
    
    # Workpiece boundaries (with offsets)
    # Left boundary: PROGRAM_OFFSET_X + STOCK_EXTENT_X_NEG
    # Right boundary: PROGRAM_OFFSET_X + STOCK_EXTENT_X_NEG + WORKPIECE_LENGTH
    workpiece_left = config.PROGRAM_OFFSET_X + config.STOCK_EXTENT_X_NEG
    workpiece_right = config.PROGRAM_OFFSET_X + config.STOCK_EXTENT_X_NEG + (config.WORKPIECE_LENGTH or 0)
    workpiece_center = (workpiece_left + workpiece_right) / 2.0
    
    # Determine compensation based on position
    # Use 10% of workpiece width as threshold for left/right detection
    threshold = (config.WORKPIECE_LENGTH or 0) * 0.1
    
    if avg_x < workpiece_left - threshold:
        return "WRKL"  # Contour is to the left of workpiece
    elif avg_x > workpiece_right + threshold:
        return "WRKR"  # Contour is to the right of workpiece
    else:
        return "NoWRK"  # Contour is centered or inside workpiece



