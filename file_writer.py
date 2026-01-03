"""
File writer module for WoodWOP Post Processor.
Handles cleaning and writing MPR files with correct encoding and line endings.
MPR files MUST use CRLF line endings regardless of operating system.
"""

import os
import re


def clean_mpr_content(content):
    """
    Clean MPR content by removing extra line endings and normalizing to single CRLF.
    
    Aggressively removes all CR CR sequences and ensures only single CRLF between lines.
    Works correctly on Windows, Linux, and macOS.
    
    Args:
        content (str): Raw MPR content (may contain mixed line endings)
        
    Returns:
        str: Cleaned content with normalized CRLF line endings
    """
    if not isinstance(content, str):
        raise TypeError(f"Content must be a string, got {type(content).__name__}")
    
    if not content:
        return ""
    
    # Step 1: Remove ALL double CR sequences first (CR CR)
    # This must be done before any other normalization
    while '\r\r' in content:
        content = content.replace('\r\r', '\r')
    
    # Step 2: Remove CR CR LF sequences specifically
    content = content.replace('\r\r\n', '\r\n')
    
    # Step 3: Normalize all line endings to LF first
    # This handles CR, CRLF, and LF uniformly
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Step 4: Split into lines and clean each line
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove trailing whitespace
        cleaned_line = line.rstrip(' \t')
        
        # Preserve empty lines (they are intentional separators between sections)
        # Only skip empty lines if previous line was also empty (to prevent triple+ empty lines)
        if cleaned_line == '':
            # Add empty line if previous line was not empty (preserve single empty lines)
            if not cleaned_lines or cleaned_lines[-1] != '':
                cleaned_lines.append('')
        else:
            cleaned_lines.append(cleaned_line)
    
    # Step 5: Join with CRLF (single CRLF between lines)
    result = '\r\n'.join(cleaned_lines)
    
    # Step 6: Final cleanup - remove any remaining CR CR sequences
    while '\r\r' in result:
        result = result.replace('\r\r', '\r')
    
    # Step 7: Remove triple+ CRLF sequences
    result = re.sub(r'(\r\n){3,}', '\r\n\r\n', result)
    
    # Step 8: Ensure file ends with CRLF (if not empty)
    if result and not result.endswith('\r\n'):
        result += '\r\n'
    
    return result


def write_mpr_file(filename, content):
    """
    Write MPR file with correct encoding (cp1252) and line endings (CRLF).
    
    Uses binary mode to prevent OS from converting CRLF to LF.
    Works correctly on Windows, Linux, and macOS.
    
    CRITICAL: Uses binary mode ("wb") to prevent Python from converting line endings.
    If you use text mode with newline="\\r\\n", Python will replace each \\n with \\r\\n,
    causing \\r\\r\\n (CR CR LF) sequences.
    
    Args:
        filename (str): Path to the output file
        content (str): MPR file content (will be cleaned before writing)
        
    Returns:
        bool: True if file was written successfully
        
    Raises:
        IOError: If file cannot be written
        UnicodeEncodeError: If content cannot be encoded in cp1252
    """
    if not isinstance(content, str):
        raise TypeError(f"Content must be a string, got {type(content).__name__}")
    
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Clean content first (removes CR CR sequences)
    cleaned_content = clean_mpr_content(content)
    
    # CRITICAL: Final verification - check for CR CR sequences
    if '\r\r' in cleaned_content:
        # Log warning and fix
        try:
            import FreeCAD
            if FreeCAD:
                FreeCAD.Console.PrintWarning(
                    "WoodWOP: Found CR CR sequences in cleaned content, removing...\n"
                )
        except:
            pass
        # Remove all double CR
        while '\r\r' in cleaned_content:
            cleaned_content = cleaned_content.replace('\r\r', '\r')
    
    # Write file in binary mode to prevent OS from modifying line endings
    # CRITICAL: Binary mode ensures CRLF is written exactly as specified
    # Using text mode with newline="\\r\\n" causes Python to replace \\n with \\r\\n,
    # resulting in \\r\\r\\n (CR CR LF) sequences
    with open(filename, "wb") as f:
        # Encode content to cp1252
        # Use 'replace' error handling to replace unencodable characters
        encoded_content = cleaned_content.encode("cp1252", errors="replace")
        f.write(encoded_content)
    
    return True


def verify_mpr_content(content):
    """
    Verify that MPR content has correct format.
    
    Args:
        content (str): Content to verify
        
    Returns:
        tuple: (is_valid, issues_list)
    """
    if not isinstance(content, str):
        return False, ["Content is not a string"]
    
    issues = []
    
    # Check for CR CR sequences
    if '\r\r' in content:
        cr_count = content.count('\r\r')
        issues.append(f"Found {cr_count} CR CR sequences (should be single CR)")
    
    # Check for CR CR LF sequences
    if '\r\r\n' in content:
        cr_cr_lf_count = content.count('\r\r\n')
        issues.append(f"Found {cr_cr_lf_count} CR CR LF sequences (should be CR LF)")
    
    # Check for LF without CR
    if '\n' in content and '\r\n' not in content:
        issues.append("Found LF (\\n) without CR - should be CRLF (\\r\\n)")
    
    # Check for standalone CR
    if '\r' in content and '\r\n' not in content:
        issues.append("Found CR (\\r) without LF - should be CRLF (\\r\\n)")
    
    is_valid = len(issues) == 0
    return is_valid, issues

