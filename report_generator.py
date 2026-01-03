"""
Report generator module for WoodWOP Post Processor.
Handles generation of job reports and analysis files.
"""

import datetime
from . import config
from . import geometry
from . import utils


def get_float_value(value):
    """
    Extract float value from Quantity object or return as-is if already float.
    
    Args:
        value: Value to extract (can be Quantity, float, or None)
        
    Returns:
        float: Extracted float value
    """
    if value is None:
        return 0.0
    if hasattr(value, 'Value'):
        # If Value itself is a Quantity, recurse
        val = value.Value
        if hasattr(val, 'Value'):
            return get_float_value(val)
        return float(val)
    return float(value)


def create_job_report(job, report_filename):
    """
    Create a detailed report of all Job properties.
    
    Args:
        job: FreeCAD Job object
        report_filename: Path to output report file
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("FreeCAD Path Job Properties Report")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Post Processor: WoodWOP MPR")
    report_lines.append("")
    
    # Basic Job information
    report_lines.append("-" * 80)
    report_lines.append("BASIC INFORMATION")
    report_lines.append("-" * 80)
    if hasattr(job, 'Label'):
        report_lines.append(f"Label: {job.Label}")
    if hasattr(job, 'Name'):
        report_lines.append(f"Name: {job.Name}")
    if hasattr(job, 'TypeId'):
        report_lines.append(f"TypeId: {job.TypeId}")
    report_lines.append("")
    
    # All properties
    report_lines.append("-" * 80)
    report_lines.append("ALL PROPERTIES")
    report_lines.append("-" * 80)
    
    if hasattr(job, 'PropertiesList'):
        for prop_name in sorted(job.PropertiesList):
            try:
                prop_value = getattr(job, prop_name, None)
                
                # Format value based on type
                if prop_value is None:
                    value_str = "None"
                elif isinstance(prop_value, (list, tuple)):
                    value_str = f"[{', '.join(str(v) for v in prop_value)}]"
                elif isinstance(prop_value, dict):
                    value_str = f"{{{', '.join(f'{k}: {v}' for k, v in prop_value.items())}}}"
                elif hasattr(prop_value, 'Value'):
                    value_str = f"{prop_value.Value} {prop_value.Unit if hasattr(prop_value, 'Unit') else ''}"
                elif hasattr(prop_value, 'Label'):
                    value_str = f"{prop_value.Label} (Name: {prop_value.Name if hasattr(prop_value, 'Name') else 'N/A'})"
                else:
                    value_str = str(prop_value)
                
                # Truncate very long values
                if len(value_str) > 200:
                    value_str = value_str[:200] + "... (truncated)"
                
                report_lines.append(f"{prop_name}: {value_str}")
            except Exception as e:
                report_lines.append(f"{prop_name}: <Error reading property: {e}>")
    else:
        report_lines.append("PropertiesList not available")
    
    report_lines.append("")
    
    # Special properties of interest
    report_lines.append("-" * 80)
    report_lines.append("SPECIAL PROPERTIES OF INTEREST")
    report_lines.append("-" * 80)
    
    special_props = [
        'PostProcessorOutputFile',
        'Model',
        'ModelName',
        'модел',
        'Base',
        'Stock',
        'ToolController',
        'Operations',
        'SetupSheet',
        'CutMaterial',
    ]
    
    for prop_name in special_props:
        if hasattr(job, prop_name):
            try:
                prop_value = getattr(job, prop_name, None)
                if prop_value is not None:
                    if hasattr(prop_value, 'Label'):
                        report_lines.append(f"{prop_name}: {prop_value.Label} (Name: {prop_value.Name if hasattr(prop_value, 'Name') else 'N/A'})")
                    elif isinstance(prop_value, (list, tuple)):
                        report_lines.append(f"{prop_name}: List/Tuple with {len(prop_value)} items")
                        for idx, item in enumerate(prop_value[:10]):
                            if hasattr(item, 'Label'):
                                report_lines.append(f"  [{idx}]: {item.Label}")
                            else:
                                report_lines.append(f"  [{idx}]: {item}")
                        if len(prop_value) > 10:
                            report_lines.append(f"  ... and {len(prop_value) - 10} more items")
                    else:
                        report_lines.append(f"{prop_name}: {prop_value}")
            except Exception as e:
                report_lines.append(f"{prop_name}: <Error: {e}>")
        else:
            report_lines.append(f"{prop_name}: <Not found>")
    
    report_lines.append("")
    
    # Stock information
    stock_extent_x_neg = 0.0
    stock_extent_x_pos = 0.0
    stock_extent_y_neg = 0.0
    stock_extent_y_pos = 0.0
    stock_extent_z_neg = 0.0
    stock_extent_z_pos = 0.0
    
    if hasattr(job, 'Stock') and job.Stock:
        report_lines.append("-" * 80)
        report_lines.append("STOCK INFORMATION")
        report_lines.append("-" * 80)
        stock = job.Stock
        if hasattr(stock, 'PropertiesList'):
            for prop_name in sorted(stock.PropertiesList):
                try:
                    prop_value = getattr(stock, prop_name, None)
                    if prop_value is not None:
                        if hasattr(prop_value, 'Value'):
                            value_str = f"{prop_value.Value} {prop_value.Unit if hasattr(prop_value, 'Unit') else ''}"
                        else:
                            value_str = str(prop_value)
                        report_lines.append(f"Stock.{prop_name}: {value_str}")
                except Exception as e:
                    report_lines.append(f"Stock.{prop_name}: <Error: {e}>")
        
        # Extract stock extents
        if hasattr(stock, 'ExtentXNeg') or hasattr(stock, 'ExtXneg'):
            stock_extent_x_neg = getattr(stock, 'ExtentXNeg', getattr(stock, 'ExtXneg', None))
        if hasattr(stock, 'ExtentXPos') or hasattr(stock, 'ExtXpos'):
            stock_extent_x_pos = getattr(stock, 'ExtentXPos', getattr(stock, 'ExtXpos', None))
        if hasattr(stock, 'ExtentYNeg') or hasattr(stock, 'ExtYneg'):
            stock_extent_y_neg = getattr(stock, 'ExtentYNeg', getattr(stock, 'ExtYneg', None))
        if hasattr(stock, 'ExtentYPos') or hasattr(stock, 'ExtYpos'):
            stock_extent_y_pos = getattr(stock, 'ExtentYPos', getattr(stock, 'ExtYpos', None))
        if hasattr(stock, 'ExtentZNeg') or hasattr(stock, 'ExtZneg'):
            stock_extent_z_neg = getattr(stock, 'ExtentZNeg', getattr(stock, 'ExtZneg', None))
        if hasattr(stock, 'ExtentZPos') or hasattr(stock, 'ExtZpos'):
            stock_extent_z_pos = getattr(stock, 'ExtentZPos', getattr(stock, 'ExtZpos', None))
    
    report_lines.append("")
    
    # Convert all values to float
    workpiece_length_val = get_float_value(config.WORKPIECE_LENGTH)
    workpiece_width_val = get_float_value(config.WORKPIECE_WIDTH)
    workpiece_thickness_val = get_float_value(config.WORKPIECE_THICKNESS)
    
    stock_extent_x_neg = get_float_value(stock_extent_x_neg)
    stock_extent_x_pos = get_float_value(stock_extent_x_pos)
    stock_extent_y_neg = get_float_value(stock_extent_y_neg)
    stock_extent_y_pos = get_float_value(stock_extent_y_pos)
    stock_extent_z_neg = get_float_value(stock_extent_z_neg)
    stock_extent_z_pos = get_float_value(stock_extent_z_pos)
    
    # Workpiece dimensions and oversizes section
    report_lines.append("-" * 80)
    report_lines.append("WORKPIECE DIMENSIONS AND OVERSIZES")
    report_lines.append("-" * 80)
    report_lines.append(f"Workpiece Length (X): {workpiece_length_val:.3f} mm")
    report_lines.append(f"Workpiece Width (Y):  {workpiece_width_val:.3f} mm")
    report_lines.append(f"Workpiece Thickness (Z): {workpiece_thickness_val:.3f} mm")
    report_lines.append("")
    report_lines.append("Stock Oversizes (Material Allowances):")
    report_lines.append(f"  X- (negative direction): {stock_extent_x_neg:.3f} mm")
    report_lines.append(f"  X+ (positive direction): {stock_extent_x_pos:.3f} mm")
    report_lines.append(f"  Y- (negative direction): {stock_extent_y_neg:.3f} mm")
    report_lines.append(f"  Y+ (positive direction): {stock_extent_y_pos:.3f} mm")
    report_lines.append(f"  Z- (negative direction): {stock_extent_z_neg:.3f} mm")
    report_lines.append(f"  Z+ (positive direction): {stock_extent_z_pos:.3f} mm")
    report_lines.append("")
    report_lines.append("Total Stock Dimensions (Workpiece + Oversizes):")
    report_lines.append(f"  Total Length (X): {workpiece_length_val + stock_extent_x_neg + stock_extent_x_pos:.3f} mm")
    report_lines.append(f"  Total Width (Y):  {workpiece_length_val + stock_extent_y_neg + stock_extent_y_pos:.3f} mm")
    report_lines.append(f"  Total Thickness (Z): {workpiece_thickness_val + stock_extent_z_neg + stock_extent_z_pos:.3f} mm")
    report_lines.append("")
    
    # Part dimensions and edge positions
    report_lines.append("-" * 80)
    report_lines.append("PART DIMENSIONS AND EDGE POSITIONS (Relative to Job Coordinate System)")
    report_lines.append("-" * 80)
    
    part_length = None
    part_width = None
    part_height = None
    min_x = None
    min_y = None
    min_z = None
    max_x = None
    max_y = None
    max_z = None
    
    try:
        # Try to get dimensions from Job.Model first
        if hasattr(job, 'Model') and job.Model:
            model_obj = job.Model
            if hasattr(model_obj, 'Shape') and hasattr(model_obj.Shape, 'BoundBox'):
                bbox = model_obj.Shape.BoundBox
                part_length = get_float_value(bbox.XLength)
                part_width = get_float_value(bbox.YLength)
                part_height = get_float_value(bbox.ZLength)
                min_x = get_float_value(bbox.XMin)
                min_y = get_float_value(bbox.YMin)
                min_z = get_float_value(bbox.ZMin)
                max_x = get_float_value(bbox.XMax)
                max_y = get_float_value(bbox.YMax)
                max_z = get_float_value(bbox.ZMax)
                report_lines.append("(Dimensions from Job.Model bounding box)")
            elif hasattr(model_obj, 'BoundBox'):
                bbox = model_obj.BoundBox
                part_length = get_float_value(bbox.XLength)
                part_width = get_float_value(bbox.YLength)
                part_height = get_float_value(bbox.ZLength)
                min_x = get_float_value(bbox.XMin)
                min_y = get_float_value(bbox.YMin)
                min_z = get_float_value(bbox.ZMin)
                max_x = get_float_value(bbox.XMax)
                max_y = get_float_value(bbox.YMax)
                max_z = get_float_value(bbox.ZMax)
                report_lines.append("(Dimensions from Job.Model bounding box)")
        
        # If Model not available, try Base
        if part_length is None and hasattr(job, 'Base') and job.Base:
            try:
                if isinstance(job.Base, list) and len(job.Base) > 0:
                    base_obj = job.Base[0]
                elif hasattr(job.Base, 'Shape'):
                    base_obj = job.Base
                else:
                    base_obj = None
                
                if base_obj and hasattr(base_obj, 'Shape') and hasattr(base_obj.Shape, 'BoundBox'):
                    bbox = base_obj.Shape.BoundBox
                    part_length = get_float_value(bbox.XLength)
                    part_width = get_float_value(bbox.YLength)
                    part_height = get_float_value(bbox.ZLength)
                    min_x = get_float_value(bbox.XMin)
                    min_y = get_float_value(bbox.YMin)
                    min_z = get_float_value(bbox.ZMin)
                    max_x = get_float_value(bbox.XMax)
                    max_y = get_float_value(bbox.YMax)
                    max_z = get_float_value(bbox.ZMax)
                    report_lines.append("(Dimensions from Job.Base bounding box)")
            except Exception as e:
                pass
        
        # If still not available, calculate from contours (fallback)
        if part_length is None:
            try:
                min_x, min_y, min_z, max_x, max_y, max_z = geometry.calculate_part_bounds()
                min_x = get_float_value(min_x)
                min_y = get_float_value(min_y)
                min_z = get_float_value(min_z)
                max_x = get_float_value(max_x)
                max_y = get_float_value(max_y)
                max_z = get_float_value(max_z)
                part_length = max_x - min_x
                part_width = max_y - min_y
                part_height = max_z - min_z
                report_lines.append("(Dimensions calculated from contours - may be inaccurate)")
            except Exception as e:
                report_lines.append(f"<Error calculating part bounds from contours: {e}>")
        
        if part_length is not None:
            report_lines.append(f"Part Length (X): {part_length:.3f} mm")
            report_lines.append(f"Part Width (Y):  {part_width:.3f} mm")
            report_lines.append(f"Part Height (Z): {part_height:.3f} mm")
            report_lines.append("")
            report_lines.append("Part Edge Positions (Job Coordinate System):")
            report_lines.append(f"  X- (minimum X): {min_x:.3f} mm")
            report_lines.append(f"  X+ (maximum X): {max_x:.3f} mm")
            report_lines.append(f"  Y- (minimum Y): {min_y:.3f} mm")
            report_lines.append(f"  Y+ (maximum Y): {max_y:.3f} mm")
            report_lines.append(f"  Z- (minimum Z): {min_z:.3f} mm")
            report_lines.append(f"  Z+ (maximum Z): {max_z:.3f} mm")
            report_lines.append("")
            report_lines.append("Part Bounding Box:")
            report_lines.append(f"  From: ({min_x:.3f}, {min_y:.3f}, {min_z:.3f}) mm")
            report_lines.append(f"  To:   ({max_x:.3f}, {max_y:.3f}, {max_z:.3f}) mm")
        else:
            report_lines.append("<Could not determine part dimensions>")
    except Exception as e:
        report_lines.append(f"<Error calculating part dimensions: {e}>")
        import traceback
        report_lines.append(f"<Traceback: {traceback.format_exc()}>")
    
    report_lines.append("")
    
    # G54 Coordinate System Offset
    report_lines.append("-" * 80)
    report_lines.append("COORDINATE SYSTEM OFFSET (G54)")
    report_lines.append("-" * 80)
    if config.COORDINATE_SYSTEM:
        offset_x_val = get_float_value(config.COORDINATE_OFFSET_X)
        offset_y_val = get_float_value(config.COORDINATE_OFFSET_Y)
        offset_z_val = get_float_value(config.COORDINATE_OFFSET_Z)
        
        report_lines.append(f"Coordinate System: {config.COORDINATE_SYSTEM}")
        report_lines.append(f"Offset X: {offset_x_val:.3f} mm")
        report_lines.append(f"Offset Y: {offset_y_val:.3f} mm")
        report_lines.append(f"Offset Z: {offset_z_val:.3f} mm")
        report_lines.append("")
        report_lines.append("NOTE: This offset is applied ONLY to MPR format coordinates.")
        report_lines.append("      G-code output remains unchanged (uses original Job coordinates).")
        if min_x is not None:
            min_x_val = get_float_value(min_x)
            min_y_val = get_float_value(min_y)
            min_z_val = get_float_value(min_z)
            
            report_lines.append("")
            report_lines.append("Part minimum point (before offset):")
            report_lines.append(f"  X: {min_x_val:.3f} mm")
            report_lines.append(f"  Y: {min_y_val:.3f} mm")
            report_lines.append(f"  Z: {min_z_val:.3f} mm")
            report_lines.append("")
            report_lines.append("Part minimum point (after G54 offset, becomes 0,0,0 in MPR):")
            report_lines.append(f"  X: {min_x_val + offset_x_val:.3f} mm (should be ~0.000)")
            report_lines.append(f"  Y: {min_y_val + offset_y_val:.3f} mm (should be ~0.000)")
            report_lines.append(f"  Z: {min_z_val + offset_z_val:.3f} mm (should be ~0.000)")
    else:
        report_lines.append("Coordinate System: Project (no offset)")
        report_lines.append("Offset X: 0.000 mm")
        report_lines.append("Offset Y: 0.000 mm")
        report_lines.append("Offset Z: 0.000 mm")
        report_lines.append("")
        report_lines.append("NOTE: No coordinate system offset is applied.")
        report_lines.append("      MPR coordinates match Job coordinates.")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("End of Report")
    report_lines.append("=" * 80)
    
    # Write report to file
    try:
        with open(report_filename, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(report_lines))
    except Exception as e:
        raise Exception(f"Failed to write report file: {e}")



