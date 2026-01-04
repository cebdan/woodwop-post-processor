"""
WoodWOP Post Processor for FreeCAD - Main Implementation
This is the main implementation using modular structure.
"""

import os
import sys
import datetime

# FreeCAD imports - only available inside FreeCAD
# Import at module level to avoid "cannot access local variable" errors
try:
    import FreeCAD
except ImportError:
    # FreeCAD not available (e.g., during testing)
    FreeCAD = None

try:
    import Path
except ImportError:
    # Path not available (e.g., during testing)
    Path = None

# Import all necessary components
# Use absolute imports when running as standalone file
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

try:
    # Try absolute import first (when running as module)
    from woodwop import config
    from woodwop import utils
    from woodwop import argument_parser
    from woodwop import path_parser
    from woodwop import geometry
    from woodwop import job_processor
    from woodwop import mpr_generator
    from woodwop import gcode_generator
    from woodwop import report_generator
    from woodwop import export_handler
except ImportError:
    # Fallback to relative imports (when running as package)
    from . import config
    from . import utils
    from . import argument_parser
    from . import path_parser
    from . import geometry
    from . import job_processor
    from . import mpr_generator
    from . import gcode_generator
    from . import report_generator
    from . import export_handler

# Re-export FreeCAD interface
TOOLTIP = config.TOOLTIP
TOOLTIP_ARGS = config.TOOLTIP_ARGS
POSTPROCESSOR_FILE_NAME = config.POSTPROCESSOR_FILE_NAME
FILE_EXTENSION = config.FILE_EXTENSION
UNITS = config.UNITS


def export(objectslist, filename, argstring):
    """
    Main export function called by FreeCAD.
    
    This is a thin wrapper that delegates to the modular post-processor.
    
    Args:
        objectslist: List of FreeCAD Path objects
        filename: Output filename (may be ignored, uses Job settings)
        argstring: Command-line arguments
        
    Returns:
        list: List of tuples [("mpr", content), ("nc", content)]
    """
    # CRITICAL: Ensure patches are applied when export is called
    # This ensures FreeCAD modules are loaded and patches are applied
    # The patch modules are self-contained and handle everything automatically
    try:
        import importlib.util
        _current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Apply command_patch (for gcode type fix)
        patch_path = os.path.join(_current_dir, 'command_patch.py')
        if os.path.exists(patch_path):
            spec = importlib.util.spec_from_file_location("command_patch", patch_path)
            if spec and spec.loader:
                patch_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(patch_module)
                # Use ensure_patch_applied() which is safe to call multiple times
                if hasattr(patch_module, 'ensure_patch_applied'):
                    patch_module.ensure_patch_applied()
                elif hasattr(patch_module, 'apply_patch'):
                    patch_module.apply_patch()
        
        # Apply dialog_patch (for .mpr extension enforcement)
        # TEMPORARILY DISABLED due to Qt import issues
        # FreeCAD will use .mpr extension based on subpart='mpr' from export() return value
        # dialog_patch_path = os.path.join(_current_dir, 'dialog_patch.py')
        # if os.path.exists(dialog_patch_path):
        #     spec = importlib.util.spec_from_file_location("dialog_patch", dialog_patch_path)
        #     if spec and spec.loader:
        #         dialog_patch_module = importlib.util.module_from_spec(spec)
        #         spec.loader.exec_module(dialog_patch_module)
        #         # Use ensure_dialog_patch_applied() which is safe to call multiple times
        #         if hasattr(dialog_patch_module, 'ensure_dialog_patch_applied'):
        #             dialog_patch_module.ensure_dialog_patch_applied()
        #         elif hasattr(dialog_patch_module, 'apply_dialog_patch'):
        #             dialog_patch_module.apply_dialog_patch()
    except Exception as e:
        # Patch failed - log but don't fail
        try:
            # Use global FreeCAD, don't import locally
            if FreeCAD:
                FreeCAD.Console.PrintWarning(
                    f"WoodWOP: Failed to ensure Command.py patches in export(): {e}\n"
                )
        except:
            pass
    # Initialize config module
    config.now = datetime.datetime.now()
    
    # Reset global state
    config.contour_counter = 1
    config.contours = []
    config.operations = []
    config.tools_used = set()
    
    # Parse arguments FIRST to set flags before any other operations
    argument_parser.parse_arguments(argstring)
    
    # Find Job object
    job = None
    job_output_file = None
    job_model = None
    part_name = None
    
    for obj in objectslist:
        if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, 'Type'):
            if 'Job' in obj.Proxy.Type:
                job = obj
                if hasattr(obj, 'PostProcessorOutputFile'):
                    job_output_file = obj.PostProcessorOutputFile
                if hasattr(obj, 'Model'):
                    job_model = obj.Model
                elif hasattr(obj, 'ModelName'):
                    job_model = obj.ModelName
                elif hasattr(obj, 'модел'):
                    job_model = obj.модел
                if hasattr(obj, 'Base') and obj.Base:
                    if hasattr(obj.Base, 'Label'):
                        part_name = obj.Base.Label
                    elif isinstance(obj.Base, (list, tuple)) and len(obj.Base) > 0:
                        if hasattr(obj.Base[0], 'Label'):
                            part_name = obj.Base[0].Label
                break
    
    # Also try to get Job from ActiveDocument if not found
    if not job and FreeCAD:
        try:
            doc = FreeCAD.ActiveDocument
            if doc:
                for obj in doc.Objects:
                    if hasattr(obj, 'Proxy') and 'Job' in str(type(obj.Proxy)):
                        job = obj
                        if hasattr(obj, 'PostProcessorOutputFile'):
                            job_output_file = obj.PostProcessorOutputFile
                        if hasattr(obj, 'Model'):
                            job_model = obj.Model
                        break
        except Exception as e:
            utils.debug_log(f"Could not access ActiveDocument: {e}")
    
    # Determine base filename
    base_filename = None
    if job_output_file and job_output_file.strip():
        dir_name = os.path.dirname(job_output_file)
        if dir_name and dir_name != '/' and dir_name != '.':
            base_name = os.path.splitext(os.path.basename(job_output_file))[0]
            if base_name:
                base_filename = base_name
    
    if not base_filename and job_model:
        model_str = str(job_model).strip()
        if model_str:
            base_filename = model_str
    
    if not base_filename and part_name:
        part_str = part_name.strip()
        if part_str:
            base_filename = part_str
    
    if not base_filename and job_output_file and job_output_file.strip():
        base_name = os.path.splitext(os.path.basename(job_output_file))[0]
        if base_name:
            base_filename = base_name
    
    if not base_filename and filename and filename != '-':
        if '.' in filename:
            base_filename = os.path.splitext(os.path.basename(filename))[0]
        else:
            base_filename = os.path.basename(filename)
    
    if not base_filename:
        base_filename = "export"
    
    # Get output directory
    output_dir = None
    if job_output_file and job_output_file.strip():
        if os.path.dirname(job_output_file):
            output_dir = os.path.dirname(os.path.abspath(job_output_file))
    
    if not output_dir:
        try:
            if FreeCAD:
                doc = getattr(FreeCAD, "ActiveDocument", None)
                if doc and doc.FileName:
                    output_dir = os.path.dirname(doc.FileName)
                else:
                    output_dir = os.getcwd()
            else:
                output_dir = os.getcwd()
        except:
            output_dir = os.getcwd()
    
    if not output_dir or output_dir == '/' or not os.path.isdir(output_dir):
        output_dir = os.getcwd()
    
    # Initialize workpiece dimensions from Job
    if job and hasattr(job, 'Stock') and job.Stock:
        stock = job.Stock
        try:
            if config.WORKPIECE_LENGTH is None and hasattr(stock, 'Length'):
                config.WORKPIECE_LENGTH = stock.Length.Value if hasattr(stock.Length, 'Value') else stock.Length
            if config.WORKPIECE_WIDTH is None and hasattr(stock, 'Width'):
                config.WORKPIECE_WIDTH = stock.Width.Value if hasattr(stock.Width, 'Value') else stock.Width
            if config.WORKPIECE_THICKNESS is None and hasattr(stock, 'Height'):
                config.WORKPIECE_THICKNESS = stock.Height.Value if hasattr(stock.Height, 'Value') else stock.Height
            
            # Get stock extents
            if hasattr(stock, 'ExtentXNeg'):
                config.STOCK_EXTENT_X_NEG = stock.ExtentXNeg.Value if hasattr(stock.ExtentXNeg, 'Value') else stock.ExtentXNeg
            elif hasattr(stock, 'ExtXneg'):
                config.STOCK_EXTENT_X_NEG = stock.ExtXneg.Value if hasattr(stock.ExtXneg, 'Value') else stock.ExtXneg
            
            if hasattr(stock, 'ExtentXPos'):
                config.STOCK_EXTENT_X_POS = stock.ExtentXPos.Value if hasattr(stock.ExtentXPos, 'Value') else stock.ExtentXPos
            elif hasattr(stock, 'ExtXpos'):
                config.STOCK_EXTENT_X_POS = stock.ExtXpos.Value if hasattr(stock.ExtXpos, 'Value') else stock.ExtXpos
            
            if hasattr(stock, 'ExtentYNeg'):
                config.STOCK_EXTENT_Y_NEG = stock.ExtentYNeg.Value if hasattr(stock.ExtentYNeg, 'Value') else stock.ExtentYNeg
            elif hasattr(stock, 'ExtYneg'):
                config.STOCK_EXTENT_Y_NEG = stock.ExtYneg.Value if hasattr(stock.ExtYneg, 'Value') else stock.ExtYneg
            
            if hasattr(stock, 'ExtentYPos'):
                config.STOCK_EXTENT_Y_POS = stock.ExtentYPos.Value if hasattr(stock.ExtentYPos, 'Value') else stock.ExtentYPos
            elif hasattr(stock, 'ExtYpos'):
                config.STOCK_EXTENT_Y_POS = stock.ExtYpos.Value if hasattr(stock.ExtYpos, 'Value') else stock.ExtYpos
            
            config.STOCK_EXTENT_X = config.STOCK_EXTENT_X_NEG + config.STOCK_EXTENT_X_POS
            config.STOCK_EXTENT_Y = config.STOCK_EXTENT_Y_NEG + config.STOCK_EXTENT_Y_POS
            
            # Get program offsets
            if hasattr(stock, 'Position') and stock.Position:
                pos = stock.Position
                if hasattr(pos, 'x'):
                    config.PROGRAM_OFFSET_X = pos.x.Value if hasattr(pos.x, 'Value') else pos.x
                elif hasattr(pos, 'X'):
                    config.PROGRAM_OFFSET_X = pos.X.Value if hasattr(pos.X, 'Value') else pos.X
                if hasattr(pos, 'y'):
                    config.PROGRAM_OFFSET_Y = pos.y.Value if hasattr(pos.y, 'Value') else pos.y
                elif hasattr(pos, 'Y'):
                    config.PROGRAM_OFFSET_Y = pos.Y.Value if hasattr(pos.Y, 'Value') else pos.Y
                if hasattr(pos, 'z'):
                    config.PROGRAM_OFFSET_Z = pos.z.Value if hasattr(pos.z, 'Value') else pos.z
                elif hasattr(pos, 'Z'):
                    config.PROGRAM_OFFSET_Z = pos.Z.Value if hasattr(pos.Z, 'Value') else pos.Z
            elif hasattr(stock, 'ProgramOffset'):
                prog_offset = stock.ProgramOffset
                if hasattr(prog_offset, 'x'):
                    config.PROGRAM_OFFSET_X = prog_offset.x.Value if hasattr(prog_offset.x, 'Value') else prog_offset.x
                elif hasattr(prog_offset, 'X'):
                    config.PROGRAM_OFFSET_X = prog_offset.X.Value if hasattr(prog_offset.X, 'Value') else prog_offset.X
                if hasattr(prog_offset, 'y'):
                    config.PROGRAM_OFFSET_Y = prog_offset.y.Value if hasattr(prog_offset.y, 'Value') else prog_offset.y
                elif hasattr(prog_offset, 'Y'):
                    config.PROGRAM_OFFSET_Y = prog_offset.Y.Value if hasattr(prog_offset.Y, 'Value') else prog_offset.Y
                if hasattr(prog_offset, 'z'):
                    config.PROGRAM_OFFSET_Z = prog_offset.z.Value if hasattr(prog_offset.z, 'Value') else prog_offset.z
                elif hasattr(prog_offset, 'Z'):
                    config.PROGRAM_OFFSET_Z = prog_offset.Z.Value if hasattr(prog_offset.Z, 'Value') else prog_offset.Z
        except Exception as e:
            print(f"[WoodWOP DEBUG] Could not get dimensions from Stock: {e}")
    
    # Second priority: Try to get dimensions from Job.Model (bounding box of actual part)
    if job and (config.WORKPIECE_LENGTH is None or config.WORKPIECE_WIDTH is None or config.WORKPIECE_THICKNESS is None):
        if hasattr(job, 'Model') and job.Model:
            try:
                model_obj = job.Model
                bbox = None
                
                # Try to get bounding box from Model
                if hasattr(model_obj, 'Shape') and hasattr(model_obj.Shape, 'BoundBox'):
                    bbox = model_obj.Shape.BoundBox
                elif hasattr(model_obj, 'BoundBox'):
                    bbox = model_obj.BoundBox
                elif isinstance(model_obj, (list, tuple)) and len(model_obj) > 0:
                    # Model might be a list of objects
                    first_obj = model_obj[0]
                    if hasattr(first_obj, 'Shape') and hasattr(first_obj.Shape, 'BoundBox'):
                        bbox = first_obj.Shape.BoundBox
                    elif hasattr(first_obj, 'BoundBox'):
                        bbox = first_obj.BoundBox
                
                if bbox:
                    if config.WORKPIECE_LENGTH is None:
                        config.WORKPIECE_LENGTH = bbox.XLength
                        print(f"[WoodWOP DEBUG] Detected workpiece length from Model: {config.WORKPIECE_LENGTH:.3f} mm")
                    if config.WORKPIECE_WIDTH is None:
                        config.WORKPIECE_WIDTH = bbox.YLength
                        print(f"[WoodWOP DEBUG] Detected workpiece width from Model: {config.WORKPIECE_WIDTH:.3f} mm")
                    if config.WORKPIECE_THICKNESS is None:
                        config.WORKPIECE_THICKNESS = bbox.ZLength
                        print(f"[WoodWOP DEBUG] Detected workpiece thickness from Model: {config.WORKPIECE_THICKNESS:.3f} mm")
            except Exception as e:
                print(f"[WoodWOP DEBUG] Could not get dimensions from Model: {e}")
    
    # Third priority: Try to get dimensions from Job.Base (bounding box)
    if job and (config.WORKPIECE_LENGTH is None or config.WORKPIECE_WIDTH is None or config.WORKPIECE_THICKNESS is None):
        if hasattr(job, 'Base') and job.Base:
            try:
                base_obj = None
                if isinstance(job.Base, (list, tuple)) and len(job.Base) > 0:
                    base_obj = job.Base[0]
                elif hasattr(job.Base, 'Shape'):
                    base_obj = job.Base
                elif hasattr(job.Base, 'Name'):
                    try:
                        # Use global FreeCAD imported at module level
                        if FreeCAD:
                            doc = FreeCAD.ActiveDocument
                            if doc:
                                base_obj = doc.getObject(job.Base.Name)
                    except:
                        pass
                
                if base_obj and hasattr(base_obj, 'Shape') and hasattr(base_obj.Shape, 'BoundBox'):
                    bbox = base_obj.Shape.BoundBox
                    if config.WORKPIECE_LENGTH is None:
                        config.WORKPIECE_LENGTH = bbox.XLength
                        print(f"[WoodWOP DEBUG] Detected workpiece length from Base: {config.WORKPIECE_LENGTH:.3f} mm")
                    if config.WORKPIECE_WIDTH is None:
                        config.WORKPIECE_WIDTH = bbox.YLength
                        print(f"[WoodWOP DEBUG] Detected workpiece width from Base: {config.WORKPIECE_WIDTH:.3f} mm")
                    if config.WORKPIECE_THICKNESS is None:
                        config.WORKPIECE_THICKNESS = bbox.ZLength
                        print(f"[WoodWOP DEBUG] Detected workpiece thickness from Base: {config.WORKPIECE_THICKNESS:.3f} mm")
            except Exception as e:
                print(f"[WoodWOP DEBUG] Could not get dimensions from Base: {e}")
    
    # Set defaults if still None
    if config.WORKPIECE_LENGTH is None:
        config.WORKPIECE_LENGTH = 800.0
        print(f"[WoodWOP DEBUG] Using default workpiece length: {config.WORKPIECE_LENGTH:.3f} mm")
    if config.WORKPIECE_WIDTH is None:
        config.WORKPIECE_WIDTH = 600.0
        print(f"[WoodWOP DEBUG] Using default workpiece width: {config.WORKPIECE_WIDTH:.3f} mm")
    if config.WORKPIECE_THICKNESS is None:
        config.WORKPIECE_THICKNESS = 20.0
        print(f"[WoodWOP DEBUG] Using default workpiece thickness: {config.WORKPIECE_THICKNESS:.3f} mm")
    
    # Check Work Coordinate Systems (Fixtures) from Job
    if job and hasattr(job, 'Fixtures') and job.Fixtures:
        fixtures_list = job.Fixtures
        if 'G54' in fixtures_list:
            config.COORDINATE_SYSTEM = 'G54'
        elif len(fixtures_list) > 0:
            first_fixture = fixtures_list[0]
            if first_fixture.startswith('G5'):
                config.COORDINATE_SYSTEM = first_fixture
    
    # Process all path objects to extract contours and operations
    for obj in objectslist:
        if not hasattr(obj, "Path"):
            continue
        job_processor.process_path_object(obj)
    
    # Calculate coordinate offset if G54 is set
    if config.COORDINATE_SYSTEM:
        min_x, min_y, min_z = geometry.calculate_part_minimum()
        config.COORDINATE_OFFSET_X = -min_x
        config.COORDINATE_OFFSET_Y = -min_y
        config.COORDINATE_OFFSET_Z = -min_z
        print(f"[WoodWOP DEBUG] G54 offset: X={config.COORDINATE_OFFSET_X:.3f}, Y={config.COORDINATE_OFFSET_Y:.3f}, Z={config.COORDINATE_OFFSET_Z:.3f}")
    
    # Calculate z_safe from SetupSheet
    z_safe = 20.0
    if job and hasattr(job, 'SetupSheet'):
        try:
            setup_sheet = job.SetupSheet
            if hasattr(setup_sheet, 'ClearanceHeightOffset'):
                clearance_offset = setup_sheet.ClearanceHeightOffset
                if hasattr(clearance_offset, 'Value'):
                    z_safe = float(clearance_offset.Value)
                else:
                    z_safe = float(clearance_offset)
                print(f"[WoodWOP DEBUG] z_safe from SetupSheet.ClearanceHeightOffset: {z_safe:.3f} mm")
        except Exception as e:
            print(f"[WoodWOP DEBUG] Could not get z_safe from SetupSheet: {e}")
    
    # Apply 20mm minimum unless /no_z_safe20 is used
    if not config.ENABLE_NO_Z_SAFE20 and z_safe < 20.0:
        original_z_safe = z_safe
        print(f"[WoodWOP WARNING] z_safe ({original_z_safe:.3f} mm) is less than 20mm minimum. Increasing to 20mm.")
        z_safe = 20.0
        try:
            if FreeCAD:
                # Try to use Qt message box for better user experience
                try:
                    from . import woodwop_file_dialog
                    woodwop_file_dialog.show_warning_message(
                        title="WoodWOP Warning",
                        message=f"z_safe was increased to 20mm minimum.\n\nOriginal value was {original_z_safe:.3f} mm.\nUse /no_z_safe20 flag to disable this check."
                    )
                except:
                    # Fallback to FreeCAD console
                    if hasattr(FreeCAD, 'Console'):
                        FreeCAD.Console.PrintWarning(
                            f"WoodWOP: z_safe was increased to 20mm minimum. Original value was {original_z_safe:.3f} mm. Use /no_z_safe20 flag to disable this check.\n"
                        )
        except:
            pass
    
    # Generate MPR content
    mpr_content = mpr_generator.generate_mpr_content(z_safe)
    
    # CRITICAL: Ensure mpr_content is a string, not a list
    if not isinstance(mpr_content, str):
        print(f"[WoodWOP CRITICAL ERROR] mpr_content is not a string! Type: {type(mpr_content)}")
        print(f"[WoodWOP CRITICAL ERROR] mpr_content value (first 200 chars): {str(mpr_content)[:200]}")
        if isinstance(mpr_content, list):
            print(f"[WoodWOP CRITICAL ERROR] mpr_content is a list with {len(mpr_content)} items")
            # Convert list to string using CRLF for MPR format
            mpr_content = '\r\n'.join(str(item) for item in mpr_content)
            print(f"[WoodWOP CRITICAL ERROR] Converted list to string, length: {len(mpr_content)}")
        else:
            mpr_content = str(mpr_content) if mpr_content else ""
            print(f"[WoodWOP CRITICAL ERROR] Converted to string, length: {len(mpr_content)}")
    
    # Final check - MUST be string
    if not isinstance(mpr_content, str):
        print(f"[WoodWOP CRITICAL ERROR] mpr_content is STILL not a string after conversion! Type: {type(mpr_content)}")
        mpr_content = str(mpr_content) if mpr_content else ""
    
    print(f"[WoodWOP DEBUG] mpr_content final type: {type(mpr_content).__name__}, length: {len(mpr_content)}")
    
    # Generate G-code if requested
    gcode_content = None
    if config.OUTPUT_NC_FILE:
        gcode_content = gcode_generator.generate_gcode(objectslist)
        # CRITICAL: Ensure gcode_content is a string, not a list
        if not isinstance(gcode_content, str):
            print(f"[WoodWOP ERROR] gcode_content is not a string! Type: {type(gcode_content)}")
            if isinstance(gcode_content, list):
                gcode_content = '\n'.join(gcode_content)
            else:
                gcode_content = str(gcode_content) if gcode_content else ""
    
    # Create job report if requested
    if config.ENABLE_JOB_REPORT and job:
        try:
            report_filename = os.path.join(output_dir, f"{base_filename}_job_report.txt")
            report_generator.create_job_report(job, report_filename)
        except Exception as e:
            print(f"[WoodWOP WARNING] Failed to create job report: {e}")
    
    # Export path commands if requested
    if config.ENABLE_PATH_COMMANDS_EXPORT:
        try:
            commands_filename = os.path.join(output_dir, f"{base_filename}_path_commands.txt")
            export_handler.export_path_commands(objectslist, commands_filename)
        except Exception as e:
            print(f"[WoodWOP WARNING] Failed to export path commands: {e}")
    
    # Return results - CRITICAL: content must be strings, not lists
    # Build result list with guaranteed string content
    result = []
    
    # CRITICAL: Force convert mpr_content to string before adding
    if isinstance(mpr_content, list):
        print(f"[WoodWOP CRITICAL ERROR] mpr_content is STILL a list before adding to result! Converting...")
        mpr_content = '\r\n'.join(str(item) for item in mpr_content)
    elif not isinstance(mpr_content, str):
        print(f"[WoodWOP CRITICAL ERROR] mpr_content is not a string before adding to result! Type: {type(mpr_content)}, converting...")
        mpr_content = str(mpr_content) if mpr_content else ""
    
    # Add MPR content (guaranteed to be string after checks above)
    result.append(("mpr", mpr_content))
    
    # Add G-code content if requested (guaranteed to be string after checks above)
    if gcode_content:
        # CRITICAL: Force convert gcode_content to string before adding
        if isinstance(gcode_content, list):
            print(f"[WoodWOP CRITICAL ERROR] gcode_content is STILL a list before adding to result! Converting...")
            gcode_content = '\n'.join(str(item) for item in gcode_content)
        elif not isinstance(gcode_content, str):
            print(f"[WoodWOP CRITICAL ERROR] gcode_content is not a string before adding to result! Type: {type(gcode_content)}, converting...")
            gcode_content = str(gcode_content) if gcode_content else ""
        result.append(("nc", gcode_content))
    
    # Final validation: ensure all content is string (triple-check)
    for idx, (subpart, content) in enumerate(result):
        # CRITICAL: Check type BEFORE any operations
        if not isinstance(content, str):
            print(f"[WoodWOP CRITICAL ERROR] result[{idx}] content is not a string! Type: {type(content)}, value: {repr(content)[:200]}")
            # Force conversion to string
            if isinstance(content, list):
                print(f"[WoodWOP CRITICAL ERROR] result[{idx}] content is a list with {len(content)} items, converting to string...")
                content = '\r\n'.join(str(item) for item in content) if subpart == 'mpr' else '\n'.join(str(item) for item in content)
            else:
                content = str(content) if content else ""
            result[idx] = (subpart, content)
            print(f"[WoodWOP CRITICAL ERROR] After conversion: type={type(content).__name__}, length={len(content)}")
        # Verify it's not empty
        if len(content) == 0:
            print(f"[WoodWOP WARNING] result[{idx}] content is empty string!")
    
    # Final debug output with type verification
    print(f"[WoodWOP DEBUG] Returning result: {len(result)} items")
    for idx, (subpart, content) in enumerate(result):
        content_type = type(content).__name__
        content_len = len(content) if content else 0
        is_string = isinstance(content, str)
        print(f"[WoodWOP DEBUG]   result[{idx}]: subpart='{subpart}', content type={content_type}, length={content_len}, is_string={is_string}")
        # CRITICAL: Ensure subpart is 'mpr' for MPR files (not 'nc')
        if idx == 0 and subpart != 'mpr':
            print(f"[WoodWOP WARNING] First subpart is '{subpart}', should be 'mpr'! Fixing...")
            result[idx] = ('mpr', content)
            subpart = 'mpr'
        if not is_string:
            print(f"[WoodWOP CRITICAL ERROR] result[{idx}] content is STILL not a string after all conversions!")
            print(f"[WoodWOP CRITICAL ERROR] Content value (first 500 chars): {repr(content)[:500]}")
            # Last resort: force conversion
            if isinstance(content, list):
                content = '\r\n'.join(str(item) for item in content) if subpart == 'mpr' else '\n'.join(str(item) for item in content)
            else:
                content = str(content) if content else ""
            result[idx] = (subpart, content)
            print(f"[WoodWOP CRITICAL ERROR] Final conversion: type={type(content).__name__}, length={len(content)}")
    
    # ABSOLUTE FINAL CHECK: Verify every item is a tuple with string content
    final_result = []
    for idx, item in enumerate(result):
        if not isinstance(item, tuple) or len(item) != 2:
            print(f"[WoodWOP CRITICAL ERROR] result[{idx}] is not a tuple of 2 elements! Type: {type(item)}, value: {item}")
            continue
        subpart, content = item
        # CRITICAL: Ensure first item has subpart='mpr' for MPR files
        if idx == 0 and subpart != 'mpr':
            print(f"[WoodWOP WARNING] First subpart is '{subpart}', should be 'mpr'! Fixing...")
            subpart = 'mpr'
        if not isinstance(content, str):
            print(f"[WoodWOP CRITICAL ERROR] FINAL CHECK: result[{idx}] content is not a string! Type: {type(content)}")
            if isinstance(content, list):
                content = '\r\n'.join(str(item) for item in content) if subpart == 'mpr' else '\n'.join(str(item) for item in content)
            else:
                content = str(content) if content else ""
        final_result.append((subpart, content))
    
    print(f"[WoodWOP DEBUG] Final result: {len(final_result)} items, all verified as strings")
    for idx, (subpart, content) in enumerate(final_result):
        print(f"[WoodWOP DEBUG]   final_result[{idx}]: subpart='{subpart}', content length={len(content)}")
    return final_result


def linenumber():
    """Not used in MPR format."""
    return utils.linenumber()
