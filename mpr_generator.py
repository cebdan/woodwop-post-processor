"""
MPR generator module for WoodWOP Post Processor.
Handles generation of MPR format content.
"""

import math
from . import config
from . import utils
from . import geometry

# Try to import file_writer for content cleaning
try:
    from . import file_writer
    HAS_FILE_WRITER = True
except ImportError:
    HAS_FILE_WRITER = False

# This module will be gradually refactored from the original generate_mpr_content function
# For now, it imports from the original file for backward compatibility

def generate_mpr_content(z_safe=20.0):
    """
    Generate complete MPR format content and return as string.
    
    NOTE: If COORDINATE_SYSTEM is set (G54, G55, etc.), coordinates will be offset
    by the minimum part coordinates. This offset is applied ONLY to MPR format.
    G-code generation is NOT affected and remains unchanged.
    
    Args:
        z_safe: Safe height value for UF and ZS parameters (default: 20.0 mm)
        
    Returns:
        str: Complete MPR file content
    """
    output = []

    # Initialize processing analysis file if enabled
    analysis_lines = []
    if config.ENABLE_PROCESSING_ANALYSIS:
        analysis_lines.append("Processing Analysis - Path Commands | Analysis | MPR Output")
        analysis_lines.append("=" * 120)

    # Header section [H
    output.append('[H')
    output.append('VERSION="4.0 Alpha"')
    output.append('WW="9.0.152"')
    output.append('OP="1"')
    output.append('WRK2="0"')
    output.append('SCHN="0"')
    output.append('CVR="0"')
    output.append('POI="0"')
    output.append('HSP="0"')
    output.append('O2="0"')
    output.append('O4="0"')
    output.append('O3="0"')
    output.append('O5="0"')
    output.append('SR="0"')
    output.append('FM="1"')
    output.append('ML="2000"')
    output.append('UF="z_safe"')
    output.append('ZS="z_safe"')
    output.append('DN="STANDARD"')
    output.append('DST="0"')
    output.append('GP="0"')
    output.append('GY="0"')
    output.append('GXY="0"')
    output.append('NP="1"')
    output.append('NE="0"')
    output.append('NA="0"')
    output.append('BFS="0"')
    output.append('US="0"')
    output.append('CB="0"')
    output.append('UP="0"')
    output.append('DW="0"')
    output.append('MAT="HOMAG"')
    output.append('HP_A_O="STANDARD"')
    output.append('OVD_U="1"')
    output.append('OVD="0"')
    output.append('OHD_U="0"')
    output.append('OHD="2"')
    output.append('OOMD_U="0"')
    output.append('EWL="1"')
    output.append('INCH="0"')
    output.append('VIEW="NOMIRROR"')
    output.append('ANZ="1"')
    output.append('BES="0"')
    output.append('ENT="0"')
    output.append('MATERIAL=""')
    output.append('CUSTOMER=""')
    output.append('ORDER=""')
    output.append('ARTICLE=""')
    output.append('PARTID=""')
    output.append('PARTTYPE=""')
    output.append('MPRCOUNT="1"')
    output.append('MPRNUMBER="1"')
    output.append('INFO1=""')
    output.append('INFO2=""')
    output.append('INFO3=""')
    output.append('INFO4=""')
    output.append('INFO5=""')
    # _BSX, _BSY, _BSZ are base dimensions (workpiece dimensions)
    # MPR header variables require 6 decimal places
    output.append(f'_BSX={utils.fmt6(config.WORKPIECE_LENGTH)}')
    output.append(f'_BSY={utils.fmt6(config.WORKPIECE_WIDTH)}')
    output.append(f'_BSZ={utils.fmt6(config.WORKPIECE_THICKNESS)}')
    # _FNX, _FNY are front offsets (left and front offsets = l_off and f_off)
    output.append(f'_FNX={utils.fmt6(config.STOCK_EXTENT_X_NEG)}')
    output.append(f'_FNY={utils.fmt6(config.STOCK_EXTENT_Y_NEG)}')
    # _RNX, _RNY, _RNZ are program offsets
    output.append(f'_RNX={utils.fmt6(config.PROGRAM_OFFSET_X)}')
    output.append(f'_RNY={utils.fmt6(config.PROGRAM_OFFSET_Y)}')
    output.append(f'_RNZ={utils.fmt6(config.PROGRAM_OFFSET_Z)}')
    # _RX and _RY are total stock dimensions: l_off + l + r_oz and f_off + w + b_oz
    output.append(f'_RX={utils.fmt6(config.STOCK_EXTENT_X_NEG + config.WORKPIECE_LENGTH + config.STOCK_EXTENT_X_POS)}')
    output.append(f'_RY={utils.fmt6(config.STOCK_EXTENT_Y_NEG + config.WORKPIECE_WIDTH + config.STOCK_EXTENT_Y_POS)}')
    output.append('')

    # Variables and workpiece section
    # Variables in [001 section use standard precision (3 decimal places)
    # CRITICAL: [001 section must come BEFORE contours (]1, ]2, etc.)
    output.append('[001')
    output.append(f'l="{utils.fmt(config.WORKPIECE_LENGTH)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="length in X"')
    output.append(f'w="{utils.fmt(config.WORKPIECE_WIDTH)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="width in Y"')
    output.append(f'th="{utils.fmt(config.WORKPIECE_THICKNESS)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="thickness in Z"')
    output.append(f'x="{utils.fmt(config.PROGRAM_OFFSET_X)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="offset programs in x"')
    output.append(f'y="{utils.fmt(config.PROGRAM_OFFSET_Y)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="offset programs in y"')
    output.append(f'z="{utils.fmt(config.PROGRAM_OFFSET_Z)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="z offset"')
    output.append(f'l_off="{utils.fmt(config.STOCK_EXTENT_X_NEG)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="left offset"')
    output.append(f'f_off="{utils.fmt(config.STOCK_EXTENT_Y_NEG)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="front offset"')
    output.append(f'r_oz="{utils.fmt(config.STOCK_EXTENT_X_POS)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="right oversize"')
    output.append(f'b_oz="{utils.fmt(config.STOCK_EXTENT_Y_POS)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="back oversize"')
    output.append(f'z_safe="{utils.fmt(z_safe)}"')
    if config.OUTPUT_COMMENTS:
        output.append('KM="clearance height"')
    output.append('')

    # Contour elements section
    for contour in config.contours:
        output.append(f']{contour["id"]}')

        # Add starting point ($E0 KP)
        start_x, start_y, start_z = contour.get('start_pos', (0.0, 0.0, 0.0))
        start_x += config.COORDINATE_OFFSET_X
        start_y += config.COORDINATE_OFFSET_Y
        
        # Check if start_z is a string expression (e.g., "th+z_safe")
        # If it's a string, pass it as-is without offset or formatting
        # WoodWOP will calculate the expression value
        if isinstance(start_z, str):
            # Expression string - pass as-is, WoodWOP will calculate
            z_value = start_z
        else:
            # Numeric value - apply offset and format
            if not config.USE_Z_PART:
                start_z += config.COORDINATE_OFFSET_Z
            z_value = utils.fmt(start_z)

        output.append('$E0')
        output.append('KP ')
        output.append(f'X={utils.fmt(start_x)}')
        output.append(f'Y={utils.fmt(start_y)}')
        output.append(f'Z={z_value}')
        output.append('KO=00')
        output.append('.X=0.000000')
        output.append('.Y=0.000000')
        output.append('.Z=0.000000')
        output.append('.KO=00')
        output.append('')

        # Add contour elements
        # Store original (unoffset) coordinates for arc center calculations
        start_pos_orig = contour.get('start_pos', (0.0, 0.0, 0.0))
        prev_elem_x_orig = start_pos_orig[0]
        prev_elem_y_orig = start_pos_orig[1]
        prev_elem_z_orig = start_pos_orig[2]
        
        # Offset coordinates for output
        prev_elem_x = start_x
        prev_elem_y = start_y
        # For calculations, use numeric value (0.0 if start_z is expression)
        # The actual Z value will come from first element
        if isinstance(start_z, str):
            prev_elem_z = 0.0  # Use 0.0 for calculations, expression will be in KP
        else:
            prev_elem_z = start_z
        
        for idx, elem in enumerate(contour['elements']):
            # Element number (1-based indexing)
            elem_num = idx + 1
            output.append(f'$E{elem_num}')

            if elem['type'] == 'KL':  # Line
                # Original coordinates (before offset) for Path Commands
                orig_x = elem['x']
                orig_y = elem['y']
                orig_z = elem.get('z', 0.0)
                
                elem_x = elem['x'] + config.COORDINATE_OFFSET_X
                elem_y = elem['y'] + config.COORDINATE_OFFSET_Y
                # Apply Z offset only if USE_Z_PART is False
                if config.USE_Z_PART:
                    z_value = elem.get('z', 0.0)  # Use Z from Job without offset
                else:
                    z_value = elem.get('z', 0.0) + config.COORDINATE_OFFSET_Z
                
                output.append('KL ')
                output.append(f'X={utils.fmt(elem_x)}')
                output.append(f'Y={utils.fmt(elem_y)}')
                output.append(f'Z={utils.fmt(z_value)}')
                
                # Calculate line angles
                dx = elem_x - prev_elem_x
                dy = elem_y - prev_elem_y
                dz = z_value - prev_elem_z
                
                if abs(dx) > 0.001 or abs(dy) > 0.001:
                    wi_angle = math.atan2(dy, dx)
                else:
                    wi_angle = 0.0
                
                line_length_xy = math.sqrt(dx*dx + dy*dy)
                if line_length_xy > 0.001:
                    wz_angle = math.atan2(dz, line_length_xy)
                else:
                    wz_angle = 0.0
                
                output.append(f'.X={utils.fmt(elem_x)}')
                output.append(f'.Y={utils.fmt(elem_y)}')
                output.append(f'.Z={utils.fmt(z_value)}')
                output.append(f'.WI={utils.fmt(wi_angle)}')
                output.append(f'.WZ={utils.fmt(wz_angle)}')

                # Processing analysis output
                if config.ENABLE_PROCESSING_ANALYSIS:
                    move_type = elem.get('move_type', 'G1')
                    line_length = math.sqrt(dx*dx + dy*dy + dz*dz)
                    path_cmd = f"{move_type} X={orig_x} Y={orig_y} Z={orig_z}"
                    analysis = f"l={line_length:.6f} r1= r2= angle="
                    mpr_output = f"{contour['id']}:{elem_num} KL e={utils.fmt(elem_x)},{utils.fmt(elem_y)},{utils.fmt(z_value)} l={utils.fmt(line_length)} rc= rf= OK"
                    analysis_lines.append(f"{path_cmd} | {analysis} | {mpr_output}")

                prev_elem_x = elem_x
                prev_elem_y = elem_y
                prev_elem_z = z_value
                
                # Update original coordinates for next element
                prev_elem_x_orig = orig_x
                prev_elem_y_orig = orig_y
                prev_elem_z_orig = orig_z

            elif elem['type'] == 'KA':  # Arc
                # Original coordinates (before offset) for center calculation
                orig_x = elem['x']
                orig_y = elem['y']
                orig_z = elem.get('z', 0.0)
                
                # Offset coordinates for output
                elem_x = elem['x'] + config.COORDINATE_OFFSET_X
                elem_y = elem['y'] + config.COORDINATE_OFFSET_Y
                # Apply Z offset only if USE_Z_PART is False
                if config.USE_Z_PART:
                    z_value = elem.get('z', 0.0)  # Use Z from Job without offset
                else:
                    z_value = elem.get('z', 0.0) + config.COORDINATE_OFFSET_Z
                
                # CRITICAL: Calculate arc center from I, J offsets using ORIGINAL (unoffset) coordinates
                center_x_orig = prev_elem_x_orig + elem.get('i', 0)
                center_y_orig = prev_elem_y_orig + elem.get('j', 0)
                
                # Apply offset to center coordinates for output
                center_x = center_x_orig + config.COORDINATE_OFFSET_X
                center_y = center_y_orig + config.COORDINATE_OFFSET_Y
                
                # Calculate start and end angles
                start_angle = math.atan2(prev_elem_y - center_y, prev_elem_x - center_x)
                end_angle = math.atan2(elem_y - center_y, elem_x - center_x)
                
                direction = elem.get('direction', 'CW')
                
                # Normalize angles based on direction
                if direction == 'CCW' and end_angle < start_angle:
                    end_angle += 2 * math.pi
                elif direction == 'CW' and end_angle > start_angle:
                    end_angle -= 2 * math.pi
                
                # Calculate arc angle
                arc_angle = abs(end_angle - start_angle)
                is_small_arc = arc_angle <= math.pi
                
                # Calculate radii
                radius_from_start = math.sqrt((prev_elem_x - center_x)**2 + (prev_elem_y - center_y)**2)
                radius_to_end = math.sqrt((elem_x - center_x)**2 + (elem_y - center_y)**2)
                
                # Get radius from element
                initial_radius = elem.get('r', 0.0)
                if initial_radius <= 0.001:
                    initial_radius = (radius_from_start + radius_to_end) / 2.0
                
                radius = initial_radius
                radius_avg = (radius_from_start + radius_to_end) / 2.0
                
                if abs(radius - radius_from_start) > 0.001 or abs(radius - radius_to_end) > 0.001:
                    radius = radius_avg
                
                # Calculate chord length
                chord_length = math.sqrt((elem_x - prev_elem_x)**2 + (elem_y - prev_elem_y)**2)
                
                # Special check for 180° arcs
                if abs(arc_angle - math.pi) < 0.001:
                    iteration = 0
                    max_iterations = 10
                    while chord_length - 2 * radius > 0.0001 and iteration < max_iterations:
                        radius = chord_length / 2.0 + 0.001
                        iteration += 1
                        if iteration == 1:
                            print(f"[WoodWOP WARNING] 180° arc: radius too small for chord {chord_length:.3f}. Adjusting to {radius:.3f}")
                    
                    min_required_radius = chord_length / 2.0 + 0.001
                    if radius < min_required_radius:
                        radius = min_required_radius
                    
                    real_correction = 2 * radius - chord_length
                    if real_correction < 0:
                        radius = chord_length / 2.0 + abs(real_correction) / 2.0 + 0.001
                        real_correction = 2 * radius - chord_length
                    real_correction = max(0.0, real_correction)
                
                # Calculate DS value
                if direction == 'CW':
                    ds_value = 0 if is_small_arc else 2
                else:
                    ds_value = 1 if is_small_arc else 3
                
                # Main block
                output.append('KA ')
                output.append(f'X={utils.fmt(elem_x)}')
                output.append(f'Y={utils.fmt(elem_y)}')
                output.append(f'Z={utils.fmt(z_value)}')
                output.append(f'DS={ds_value}')
                output.append(f'R={utils.fmt(radius)}')
                
                # Calculated block
                waz_angle = 0.0
                output.append(f'.X={utils.fmt(elem_x)}')
                output.append(f'.Y={utils.fmt(elem_y)}')
                output.append(f'.Z={utils.fmt(z_value)}')
                output.append(f'.I={utils.fmt(center_x)}')
                output.append(f'.J={utils.fmt(center_y)}')
                output.append(f'.DS={ds_value}')
                output.append(f'.R={utils.fmt(radius)}')
                output.append(f'.WI={utils.fmt(start_angle)}')
                output.append(f'.WO={utils.fmt(end_angle)}')
                output.append(f'.WAZ={utils.fmt(waz_angle)}')
                
                prev_elem_x = elem_x
                prev_elem_y = elem_y
                prev_elem_z = z_value
                
                # Update original coordinates for next element
                prev_elem_x_orig = orig_x
                prev_elem_y_orig = orig_y
                prev_elem_z_orig = orig_z

            output.append('')

        output.append('')

    output.append(f'<100 \\WerkStck\\')
    output.append(f'LA="l"')
    output.append(f'BR="w"')
    output.append(f'DI="th"')
    output.append(f'FNX="l_off"')
    output.append(f'FNY="f_off"')
    output.append(f'RNX="x"')
    output.append(f'RNY="y"')
    output.append(f'RNZ="z"')
    output.append(f'RL="l_off+l+r_oz"')
    output.append(f'RB="f_off+w+b_oz"')
    output.append('')

    if config.OUTPUT_COMMENTS:
        output.append('<101 \\Kommentar\\')
        output.append(f'KM="Generated by FreeCAD WoodWOP Post Processor"')
        output.append(f'KM="Date: {config.now.strftime("%Y-%m-%d %H:%M:%S")}"')
        if config.COORDINATE_SYSTEM:
            output.append(f'KM="Coordinate System: {config.COORDINATE_SYSTEM} (offset: X={config.COORDINATE_OFFSET_X:.3f}, Y={config.COORDINATE_OFFSET_Y:.3f}, Z={config.COORDINATE_OFFSET_Z:.3f})"')
        output.append('KAT="Kommentar"')
        output.append('MNM="Kommentar"')
        output.append('ORI="1"')
        output.append('')

    # Operations section
    # ORI counter: starts from 1 (first comment), then increments for each operation comment and operation
    # First comment has ORI="1", operation comment has ORI="2", operation has ORI="3" for first operation
    operation_ori_counter = 1  # Already used for first comment (if OUTPUT_COMMENTS)
    
    for op in config.operations:
        if op['type'] == 'BohrVert':
            xa = op['xa'] + config.COORDINATE_OFFSET_X
            ya = op['ya'] + config.COORDINATE_OFFSET_Y
            
            output.append(f'<{op["id"]} \\BohrVert\\')
            output.append(f'XA="{utils.fmt(xa)}"')
            output.append(f'YA="{utils.fmt(ya)}"')
            output.append(f'TI="{utils.fmt(op["depth"])}"')
            output.append(f'TNO="{op["tool"]}"')
            output.append(f'BM="SS"')
            output.append('')

        elif op['type'] == 'Contourfraesen':
            contour = None
            for c in config.contours:
                if c['id'] == op['contour']:
                    contour = c
                    break
            
            # EE: last element number in MPR format (1-based, $E1, $E2, ..., $E14)
            # Elements are numbered from $E1 to $E{len(elements)} in MPR
            # So last element number = len(elements) (not len-1, because numbering starts from 1)
            last_element_num = 0
            if contour and contour['elements']:
                last_element_num = len(contour['elements'])  # $E1 to $E{len}, so last is len
            
            rk_value = geometry.determine_tool_compensation(op['contour'])
            
            # Add comment before operation: <101 \Kommentar\ with KAT and MNM
            operation_ori_counter += 1  # Increment for comment
            output.append('<101 \\Kommentar\\')
            output.append('KAT="Fräsen"')
            output.append(f'MNM="Vertical trimming"')
            output.append(f'ORI="{operation_ori_counter}"')
            output.append('')
            
            # Operation ID: 105 for Konturfraesen (not 101)
            operation_ori_counter += 1  # Increment for operation
            output.append(f'<105 \\Konturfraesen\\')
            # EA: start at $E1 (index 0 in list, but element number 1 in MPR)
            output.append(f'EA="{op["contour"]}:0"')
            output.append(f'MDA="SEN"')
            output.append(f'STUFEN="0"')
            output.append(f'BL="0"')
            output.append(f'WZS="1"')
            output.append(f'OSZI="0"')
            output.append(f'OSZVS="0"')
            output.append(f'ZSTART="0"')
            output.append(f'ANZZST="0"')
            output.append(f'RK="{rk_value}"')
            output.append(f'EE="{op["contour"]}:{last_element_num}"')
            output.append(f'MDE="SEN_AB"')
            output.append(f'EM="0"')
            output.append(f'RI="1"')
            output.append(f'TNO="{op["tool"]}"')
            output.append(f'SM="0"')
            output.append(f'S_="STANDARD"')
            output.append(f'F_="5"')
            output.append(f'AB="0"')
            output.append(f'AF="0"')
            output.append(f'AW="0"')
            output.append(f'BW="0"')
            output.append(f'VLS="0"')
            output.append(f'VLE="0"')
            output.append(f'ZA="@0"')
            output.append(f'SC="0"')
            output.append(f'TDM="0"')
            output.append(f'HP="0"')
            output.append(f'SP="0"')
            output.append(f'YVE="0"')
            output.append(f'WW="1,2,3,401,402,403"')
            output.append(f'ASG="2"')
            output.append(f'HP_A_O="STANDARD"')
            output.append(f'KG="0"')
            output.append(f'RP="STANDARD"')
            output.append(f'RSEL="0"')
            output.append(f'RWID="0"')
            output.append(f'KAT="Fräsen"')
            output.append(f'MNM="Vertical trimming"')
            output.append(f'ORI="{operation_ori_counter}"')
            output.append(f'MX="0"')
            output.append(f'MY="0"')
            output.append(f'MZ="0"')
            output.append(f'MXF="1"')
            output.append(f'MYF="1"')
            output.append(f'MZF="1"')
            output.append(f'SYA="0"')
            output.append(f'SYV="0"')
            output.append('')

        elif op['type'] == 'Pocket':
            # Find contour to check if G0 was added
            contour = None
            for c in config.contours:
                if c['id'] == op['contour']:
                    contour = c
                    break
            
            output.append(f'<{op["id"]} \\Pocket\\')
            # EA: start at $E1 (index 0)
            output.append(f'EA="{op["contour"]}:0"')
            output.append(f'TNO="{op["tool"]}"')
            output.append('')

    # End of file
    # Add empty line before ! if there are operations
    if config.operations:
        output.append('')
    output.append('!')

    # Save processing analysis file if enabled
    if config.ENABLE_PROCESSING_ANALYSIS and len(analysis_lines) > 0:
        try:
            import os
            import FreeCAD
            base_filename = "processing_analysis"
            try:
                doc = FreeCAD.ActiveDocument
                if doc:
                    for obj in doc.Objects:
                        if hasattr(obj, 'Proxy') and 'Job' in str(type(obj.Proxy)):
                            if hasattr(obj, 'PostProcessorOutputFile') and obj.PostProcessorOutputFile:
                                base_filename = os.path.splitext(os.path.basename(obj.PostProcessorOutputFile))[0]
                                break
                            elif hasattr(obj, 'Model') and obj.Model:
                                if hasattr(obj.Model, 'Label'):
                                    base_filename = obj.Model.Label.replace(' ', '_')
                                    break
            except:
                pass
            
            output_dir = os.getcwd()
            try:
                doc = FreeCAD.ActiveDocument
                if doc and hasattr(doc, 'FileName') and doc.FileName:
                    output_dir = os.path.dirname(doc.FileName)
            except:
                pass
            
            analysis_filename = os.path.join(output_dir, f"{base_filename}_processing_analysis.txt")
            with open(analysis_filename, 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(analysis_lines))
            print(f"[WoodWOP] Processing analysis exported to: {analysis_filename}")
        except Exception as e:
            print(f"[WoodWOP ERROR] Failed to write processing analysis file: {e}")
    
    # Return the complete MPR content as a string with CRLF line endings
    # CRITICAL: Ensure output is a list of strings before joining
    if not isinstance(output, list):
        print(f"[WoodWOP ERROR] output is not a list! Type: {type(output)}")
        if isinstance(output, str):
            return output
        else:
            output = [str(item) for item in output] if output else []
    
    # Ensure all items in output are strings
    output_strs = []
    for idx, item in enumerate(output):
        if not isinstance(item, str):
            print(f"[WoodWOP WARNING] output[{idx}] is not a string! Type: {type(item)}, converting...")
            output_strs.append(str(item))
        else:
            output_strs.append(item)
    
    # CRITICAL: Ensure we have strings to join
    if not output_strs:
        print(f"[WoodWOP WARNING] output_strs is empty, using minimal MPR")
        minimal_mpr = '[H\r\nVERSION="4.0 Alpha"\r\n]H\r\n[001\r\nz_safe=20.0\r\n]001\r\n!'
        return minimal_mpr
    
    # CRITICAL: Clean strings before joining to prevent CR CR LF sequences
    # Remove ALL \r and \n characters from ENTIRE string (not just from end!)
    # This prevents \r (anywhere in string) + \r\n (from join) = \r\r\n (CR CR LF)
    # IMPORTANT: Preserve empty strings (they are intentional separators between sections)
    cleaned_output = []
    for item in output_strs:
        # Convert to string if needed
        if not isinstance(item, str):
            item = str(item)
        
        # Remove ALL \r and \n from ENTIRE string using replace()
        # This is more aggressive than rstrip() and catches \r anywhere
        # Do NOT use strip() here - we want to preserve empty strings
        cleaned = item.replace('\r', '').replace('\n', '')
        
        # Preserve empty strings (they are intentional separators)
        # Only skip strings that are empty after removing whitespace
        if cleaned.strip() or cleaned == '':
            cleaned_output.append(cleaned)
    
    # CRITICAL: Ensure we have strings to join after cleaning
    if not cleaned_output:
        print(f"[WoodWOP WARNING] cleaned_output is empty, using minimal MPR")
        minimal_mpr = '[H\r\nVERSION="4.0 Alpha"\r\n]H\r\n[001\r\nz_safe=20.0\r\n]001\r\n!'
        return minimal_mpr
    
    # Join all cleaned strings with CRLF (single CRLF between lines)
    # Now we're sure that strings don't have trailing \r or \n
    try:
        result = '\r\n'.join(cleaned_output)
    except Exception as e:
        print(f"[WoodWOP CRITICAL ERROR] Failed to join cleaned_output: {e}")
        print(f"[WoodWOP CRITICAL ERROR] cleaned_output type: {type(cleaned_output)}")
        print(f"[WoodWOP CRITICAL ERROR] cleaned_output length: {len(cleaned_output)}")
        if cleaned_output:
            print(f"[WoodWOP CRITICAL ERROR] First item type: {type(cleaned_output[0])}")
        # Fallback: convert everything to string and clean
        cleaned_fallback = []
        for item in output_strs:
            # Remove ALL \r and \n from ENTIRE string using replace()
            # Preserve empty strings (they are intentional separators)
            cleaned = str(item).replace('\r', '').replace('\n', '')
            if cleaned.strip() or cleaned == '':
                cleaned_fallback.append(cleaned)
        result = '\r\n'.join(cleaned_fallback)
    
    # CRITICAL: Remove any remaining CR CR sequences (double CR)
    # This handles cases where \r\r\n might still exist despite cleaning
    while '\r\r' in result:
        result = result.replace('\r\r', '\r')
    
    # Ensure file ends with CRLF
    if result and not result.endswith('\r\n'):
        result += '\r\n'
    
    # Use file_writer to clean content (ensures proper CRLF and removes any remaining issues)
    # NOTE: clean_mpr_content preserves empty lines between sections
    if HAS_FILE_WRITER:
        try:
            result = file_writer.clean_mpr_content(result)
        except Exception as e:
            print(f"[WoodWOP WARNING] Failed to use file_writer.clean_mpr_content(): {e}")
            # Continue with result as-is
    
    print(f"[WoodWOP DEBUG] generate_mpr_content() result length: {len(result)} characters")
    print(f"[WoodWOP DEBUG] generate_mpr_content() result type: {type(result).__name__}")
    
    # CRITICAL: Final check - result MUST be a string
    if not isinstance(result, str):
        print(f"[WoodWOP CRITICAL ERROR] result is not a string after join! Type: {type(result)}")
        print(f"[WoodWOP CRITICAL ERROR] result value (first 500 chars): {str(result)[:500]}")
        # Force conversion
        if isinstance(result, list):
            # Remove ALL \r and \n from ENTIRE string using replace()
            cleaned_list = [str(item).replace('\r', '').replace('\n', '').strip() for item in result if str(item).strip()]
            result = '\r\n'.join(cleaned_list)
        else:
            result = str(result) if result else ""
        # Remove double CR
        while '\r\r' in result:
            result = result.replace('\r\r', '\r')
        print(f"[WoodWOP CRITICAL ERROR] After conversion: type={type(result).__name__}, length={len(result)}")
    
    if len(result) == 0:
        minimal_mpr = '[H\r\nVERSION="4.0 Alpha"\r\n]H\r\n[001\r\nz_safe=20.0\r\n]001\r\n!'
        return minimal_mpr
    
    return result

