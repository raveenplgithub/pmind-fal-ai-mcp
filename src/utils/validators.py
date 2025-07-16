"""Input validation and sanitization utilities."""

import re
from pathlib import Path

from .errors import ToolError


def validate_file_path(file_path: str) -> Path:
    """Validate and resolve file path safely.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Resolved absolute path
        
    Raises:
        ToolError: If path is invalid
    """
    try:
        path = Path(file_path).expanduser().resolve()
    except Exception as e:
        raise ToolError(f"Invalid file path: {e}")
    
    # Check if path exists
    if not path.exists():
        raise ToolError(f"File not found: {file_path}")
    
    # Check if it's a file
    if not path.is_file():
        raise ToolError(f"Path is not a file: {file_path}")
    
    return path



def sanitize_cache_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename.
    
    Args:
        name: String to sanitize
        
    Returns:
        Sanitized filename
    """
    # Replace path separators and other unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized