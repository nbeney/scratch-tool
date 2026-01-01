import json
import re
from typing import Optional


def print_colored_json(data: dict) -> None:
    """Pretty print JSON with syntax highlighting."""
    json_str = json.dumps(data, indent=4, sort_keys=True)
    colored_json = highlight(json_str, JsonLexer(), TerminalFormatter())
    typer.echo(colored_json)


def extract_project_id(url_or_id: str) -> str:
    """Extract project ID from URL or return the ID if already a number."""
    # If it's already just a number, return it
    if url_or_id.isdigit():
        return url_or_id
    
    # Try to extract ID from URL patterns
    # Matches: https://scratch.mit.edu/projects/1259204833/
    # Matches: https://scratch.mit.edu/projects/1259204833/editor
    pattern = r'scratch\.mit\.edu/projects/(\d+)'
    match = re.search(pattern, url_or_id)
    
    if match:
        return match.group(1)
    
    # If no match found, raise an error
    raise ValueError(f"Could not extract project ID from: {url_or_id}")


def sanitize_filename(filename: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Replace multiple spaces with single space
    filename = ' '.join(filename.split())
    
    # Limit length to avoid filesystem issues
    max_length = 200
    if len(filename) > max_length:
        filename = filename[:max_length].strip()
    
    # If empty after sanitization, use a default
    if not filename:
        filename = "untitled"
    
    return filename


def extract_project_id_from_filename(filename: str) -> Optional[str]:
    """
    Extract project ID from filename if it matches the pattern:
    <title>-<project_id>-project.sb3 or <title>-<project_id>-project.json
    
    Returns the project ID if found, None otherwise.
    """
    # Remove path and get just the filename
    base_name = Path(filename).stem
    
    # Pattern: anything-<digits>-project
    # The project ID is always numeric and comes before "-project"
    pattern = r'-(\d+)-project$'
    match = re.search(pattern, base_name)
    
    if match:
        return match.group(1)
    
    return None
