"""
Job processor module for WoodWOP Post Processor.
Handles processing of FreeCAD Job objects and creation of operations.
"""

from . import config
from . import path_parser
from . import geometry

# Try to import FreeCAD Path utilities
try:
    import PathScripts.PathUtils as PathUtils
except ImportError:
    PathUtils = None


def process_path_object(obj):
    """
    Process a single FreeCAD Path object.
    
    Args:
        obj: FreeCAD Path object
    """
    # Determine operation type
    op_type = get_operation_type(obj)

    if op_type == 'profile' or op_type == 'contour':
        # Create contour and routing operation
        contour_id = config.contour_counter
        config.contour_counter += 1

        contour_elements, start_pos = path_parser.extract_contour_from_path(obj)
        if contour_elements:
            config.contours.append({
                'id': contour_id,
                'elements': contour_elements,
                'start_pos': start_pos,
                'label': obj.Label if hasattr(obj, 'Label') else f'Contour{contour_id}'
            })

            # Create Contourfraesen operation
            tool_number = get_tool_number(obj)
            if tool_number:
                config.tools_used.add(tool_number)

            config.operations.append(create_contour_milling(obj, contour_id, tool_number))

    elif op_type == 'drilling':
        # Create drilling operations
        drill_ops = path_parser.extract_drilling_operations(obj, get_tool_number)
        config.operations.extend(drill_ops)

        tool_number = get_tool_number(obj)
        if tool_number:
            config.tools_used.add(tool_number)

    elif op_type == 'pocket':
        # Create contour for pocket and pocket operation
        contour_id = config.contour_counter
        config.contour_counter += 1

        contour_elements, start_pos = path_parser.extract_contour_from_path(obj)
        if contour_elements:
            config.contours.append({
                'id': contour_id,
                'elements': contour_elements,
                'start_pos': start_pos,
                'label': obj.Label if hasattr(obj, 'Label') else f'Pocket{contour_id}'
            })

            tool_number = get_tool_number(obj)
            if tool_number:
                config.tools_used.add(tool_number)

            config.operations.append(create_pocket_milling(obj, contour_id, tool_number))


def get_operation_type(obj):
    """
    Determine the type of operation from FreeCAD Path object.
    
    Args:
        obj: FreeCAD Path object
        
    Returns:
        str: Operation type ('profile', 'drilling', 'pocket', or 'contour')
    """
    if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, 'Type'):
        obj_type = obj.Proxy.Type.lower()
        if 'profile' in obj_type or 'contour' in obj_type:
            return 'profile'
        elif 'drill' in obj_type:
            return 'drilling'
        elif 'pocket' in obj_type:
            return 'pocket'

    # Fallback: analyze path commands
    if hasattr(obj, 'Path'):
        try:
            if PathUtils is None:
                path_commands = obj.Path.Commands if hasattr(obj.Path, 'Commands') else []
            else:
                path_commands = PathUtils.getPathWithPlacement(obj).Commands
            has_arcs = any(cmd.Name in ['G2', 'G02', 'G3', 'G03'] for cmd in path_commands)
            has_drilling = any(cmd.Name in ['G81', 'G82', 'G83'] for cmd in path_commands)

            if has_drilling:
                return 'drilling'
            elif has_arcs:
                return 'profile'
        except:
            # Fallback to direct Path access
            if hasattr(obj.Path, 'Commands'):
                has_arcs = any(cmd.Name in ['G2', 'G02', 'G3', 'G03'] for cmd in obj.Path.Commands)
                has_drilling = any(cmd.Name in ['G81', 'G82', 'G83'] for cmd in obj.Path.Commands)

                if has_drilling:
                    return 'drilling'
                elif has_arcs:
                    return 'profile'

    return 'contour'


def get_tool_number(obj):
    """
    Extract tool number from Path object.
    
    Args:
        obj: FreeCAD Path object
        
    Returns:
        int or None: Tool number if found, None otherwise
    """
    if hasattr(obj, 'ToolController'):
        tc = obj.ToolController
        if hasattr(tc, 'ToolNumber'):
            return tc.ToolNumber
        elif hasattr(tc, 'Tool'):
            tool = tc.Tool
            if hasattr(tool, 'ToolNumber'):
                return tool.ToolNumber
            elif hasattr(tool, 'Number'):
                return tool.Number
    return None


def create_contour_milling(obj, contour_id, tool_number):
    """
    Create Contourfraesen (contour milling) operation.
    
    Args:
        obj: FreeCAD Path object
        contour_id: ID of the contour
        tool_number: Tool number to use
        
    Returns:
        dict: Contour milling operation dictionary
    """
    # Find contour to determine last element index
    contour = None
    for c in config.contours:
        if c['id'] == contour_id:
            contour = c
            break
    
    # Determine last element index (0-based, so last is len-1)
    last_element_idx = 0
    if contour and contour['elements']:
        last_element_idx = len(contour['elements']) - 1
    
    # Determine tool compensation (RK) based on contour position
    rk_value = geometry.determine_tool_compensation(contour_id)
    
    return {
        'type': 'Contourfraesen',
        'id': 101,
        'contour': contour_id,
        'tool': tool_number if tool_number else 1,
        'rk': rk_value,
        'last_element': last_element_idx
    }


def create_pocket_milling(obj, contour_id, tool_number):
    """
    Create Pocket (pocket milling) operation.
    
    Args:
        obj: FreeCAD Path object
        contour_id: ID of the contour
        tool_number: Tool number to use
        
    Returns:
        dict: Pocket milling operation dictionary
    """
    return {
        'type': 'Pocket',
        'id': 103,
        'contour': contour_id,
        'tool': tool_number if tool_number else 1
    }



