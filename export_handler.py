"""
Export handler module for WoodWOP Post Processor.
Handles export of Path commands and other auxiliary files.
"""

from . import config
from . import utils
from . import job_processor


def export_path_commands(objectslist, output_filename):
    """
    Export all Path Commands from all operations to a text file.
    
    Args:
        objectslist: List of FreeCAD Path objects to process
        output_filename: Full path to the output file
        
    Returns:
        bool: True if file was created successfully, False otherwise
    """
    try:
        import datetime
        from PathScripts import PathUtils
        
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("FreeCAD Path Commands Export")
        output_lines.append("=" * 80)
        output_lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"Post Processor: WoodWOP MPR")
        output_lines.append("")
        
        operation_count = 0
        total_commands = 0
        
        # Process all path objects
        for obj in objectslist:
            if not hasattr(obj, "Path"):
                continue
            
            # Get operation info
            op_label = obj.Label if hasattr(obj, 'Label') else 'Unknown'
            op_type = job_processor.get_operation_type(obj)
            tool_number = job_processor.get_tool_number(obj)
            
            output_lines.append("-" * 80)
            output_lines.append(f"Operation: {op_label}")
            output_lines.append(f"Type: {op_type}")
            output_lines.append(f"Tool: {tool_number}")
            output_lines.append("-" * 80)
            output_lines.append("")
            
            # Get path commands
            try:
                path_commands = PathUtils.getPathWithPlacement(obj).Commands
            except:
                path_commands = obj.Path.Commands if hasattr(obj.Path, 'Commands') else []
            
            if not path_commands:
                output_lines.append("(No commands found)")
                output_lines.append("")
                continue
            
            # Export all commands
            command_num = 0
            for cmd in path_commands:
                command_num += 1
                total_commands += 1
                
                # Format command line
                line = f"{command_num:4d}. {cmd.Name}"
                
                # Add parameters
                if cmd.Parameters:
                    for param, value in sorted(cmd.Parameters.items()):
                        line += f" {param}{utils.fmt(value)}"
                
                output_lines.append(line)
            
            output_lines.append("")
            output_lines.append(f"Total commands in this operation: {command_num}")
            output_lines.append("")
            operation_count += 1
        
        # Summary
        output_lines.append("=" * 80)
        output_lines.append("Summary")
        output_lines.append("=" * 80)
        output_lines.append(f"Total operations: {operation_count}")
        output_lines.append(f"Total commands: {total_commands}")
        output_lines.append("")
        output_lines.append("=" * 80)
        output_lines.append("End of Export")
        output_lines.append("=" * 80)
        
        # Write to file
        with open(output_filename, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(output_lines))
        
        print(f"[WoodWOP] Path commands exported to: {output_filename}")
        print(f"[WoodWOP]   Operations: {operation_count}, Commands: {total_commands}")
        return True
        
    except Exception as e:
        print(f"[WoodWOP ERROR] Failed to export path commands: {e}")
        import traceback
        print(f"[WoodWOP ERROR] Traceback:\n{traceback.format_exc()}")
        return False



