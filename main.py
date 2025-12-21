#!/home/nbeney/.local/bin/uv run

import json
import re
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests
import typer
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer
from pydantic import ValidationError

from models.metadata import ErrorResponse, ProjectMetadata

app = typer.Typer()


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
    # Matches: https://scratch.mit.edu/projects/1252755893/
    # Matches: https://scratch.mit.edu/projects/1252755893/editor
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


@app.command()
def metadata(
    url_or_id: str = typer.Argument(..., help="Scratch project URL or ID"),
):
    """
    Fetch and display project metadata.
    
    Note: Only public and shared projects can be accessed.
    
    Examples:
        scratch-tool metadata https://scratch.mit.edu/projects/1252755893/
        scratch-tool metadata 1252755893
    """
    try:
        # Extract project ID from URL or use ID directly
        project_id = extract_project_id(url_or_id)
        typer.echo(f"Fetching metadata for project {project_id}...")
        typer.echo()
        
        # Fetch the project metadata
        api_url = f"https://api.scratch.mit.edu/projects/{project_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Try to parse as ProjectMetadata, otherwise treat as error
        try:
            project_meta = ProjectMetadata.model_validate(data)
            # Convert to dict with aliases for pretty printing
            output_data = project_meta.model_dump(by_alias=True, mode='json')
            print_colored_json(output_data)
            typer.secho("\n✓ Successfully fetched metadata", fg=typer.colors.GREEN)
        except ValidationError:
            # Check if it's an error response
            try:
                error = ErrorResponse.model_validate(data)
                typer.secho(f"Error from API: {error.code}", fg=typer.colors.RED, err=True)
                if error.message:
                    typer.secho(f"Message: {error.message}", fg=typer.colors.RED, err=True)
                else:
                    typer.secho("The project may not exist, be private, or be unshared.", fg=typer.colors.YELLOW, err=True)
                raise typer.Exit(1)
            except ValidationError:
                # Unknown response format
                typer.secho("Received unexpected response format:", fg=typer.colors.YELLOW, err=True)
                print_colored_json(data)
                raise typer.Exit(1)
                
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            typer.secho(f"Error: Project not found (404)", fg=typer.colors.RED, err=True)
            typer.secho("", err=True)
            typer.secho("This could mean:", fg=typer.colors.YELLOW, err=True)
            typer.secho("  • The project ID is incorrect", fg=typer.colors.YELLOW, err=True)
            typer.secho("  • The project is not shared or is private", fg=typer.colors.YELLOW, err=True)
            typer.secho("  • The project has been deleted", fg=typer.colors.YELLOW, err=True)
            typer.secho("", err=True)
            typer.secho("Note: Only public and shared projects can be accessed.", fg=typer.colors.CYAN, err=True)
        else:
            typer.secho(f"Error fetching metadata: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error fetching metadata: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@app.command()
def download(
    url_or_id: str = typer.Argument(..., help="Scratch project URL or ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Output filename (without extension)")
):
    """
    Download a Scratch 3 project given its URL or ID.
    
    By default, the file is named after the project title.
    Use --name to specify a custom filename.
    
    Note: Only public and shared projects can be downloaded.
    
    Examples:
        scratch-tool download https://scratch.mit.edu/projects/1252755893/
        scratch-tool download https://scratch.mit.edu/projects/1252755893/editor
        scratch-tool download 1252755893
        scratch-tool download 1252755893 --name my-project
    """
    try:
        # Extract project ID from URL or use ID directly
        project_id = extract_project_id(url_or_id)
        typer.echo(f"Downloading project {project_id}...")
        
        # First, get the project metadata to obtain the token
        api_url = f"https://api.scratch.mit.edu/projects/{project_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        typer.echo("Fetching project metadata...")
        metadata_response = requests.get(api_url, headers=headers, timeout=30)
        metadata_response.raise_for_status()
        metadata_dict = metadata_response.json()
        
        # Validate and parse metadata using Pydantic model
        try:
            project_metadata = ProjectMetadata.model_validate(metadata_dict)
        except ValidationError as e:
            # Check if it's an error response
            try:
                error = ErrorResponse.model_validate(metadata_dict)
                raise ValueError(f"API Error: {error.code}. The project may be private, unshared, or deleted.")
            except ValidationError:
                raise ValueError("Could not parse project metadata. The project may be invalid or inaccessible.")
        
        # Construct the download URL with token
        download_url = f"https://projects.scratch.mit.edu/{project_id}?token={project_metadata.project_token}"
        
        # Download the project.json
        typer.echo("Downloading project.json...")
        response = requests.get(download_url, headers=headers, timeout=30)
        response.raise_for_status()
        project_json = response.json()
        
        # Extract all asset information from the project
        typer.echo("Collecting asset information...")
        assets = []
        seen_assets = set()
        
        # Iterate through all targets (sprites and stage)
        for target in project_json.get('targets', []):
            # Get costumes
            for costume in target.get('costumes', []):
                if 'assetId' in costume and 'md5ext' in costume:
                    md5ext = costume['md5ext']
                    if md5ext not in seen_assets:
                        seen_assets.add(md5ext)
                        assets.append({
                            'id': costume['assetId'],
                            'md5ext': md5ext,
                            'type': 'costume'
                        })
            
            # Get sounds
            for sound in target.get('sounds', []):
                if 'assetId' in sound and 'md5ext' in sound:
                    md5ext = sound['md5ext']
                    if md5ext not in seen_assets:
                        seen_assets.add(md5ext)
                        assets.append({
                            'id': sound['assetId'],
                            'md5ext': md5ext,
                            'type': 'sound'
                        })
        
        # Determine output filename
        if name:
            # User provided custom name
            filename = f"{name}.sb3"
        else:
            # Use project title, sanitized for filesystem
            safe_title = sanitize_filename(project_metadata.title)
            filename = f"{safe_title}.sb3"
            typer.echo(f"Using filename: {filename}")
        
        # Create the .sb3 file as a ZIP archive
        typer.echo(f"Building .sb3 file with {len(assets)} assets...")
        output_path = Path(filename)
        
        with ZipFile(output_path, 'w') as sb3_file:
            # Write project.json
            sb3_file.writestr('project.json', json.dumps(project_json))
            
            # Download and add each asset
            for i, asset in enumerate(assets, 1):
                md5ext = asset['md5ext']
                asset_url = f"https://assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/"
                
                typer.echo(f"  Downloading asset {i}/{len(assets)}: {md5ext}")
                
                try:
                    asset_response = requests.get(asset_url, headers=headers, timeout=30)
                    asset_response.raise_for_status()
                    sb3_file.writestr(md5ext, asset_response.content)
                except requests.exceptions.RequestException as e:
                    typer.secho(f"  Warning: Failed to download asset {md5ext}: {e}", fg=typer.colors.YELLOW)
        
        typer.secho(f"✓ Successfully downloaded to {filename}", fg=typer.colors.GREEN)
        
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            typer.secho(f"Error: Project not found (404)", fg=typer.colors.RED, err=True)
            typer.secho("", err=True)
            typer.secho("This could mean:", fg=typer.colors.YELLOW, err=True)
            typer.secho("  • The project ID is incorrect", fg=typer.colors.YELLOW, err=True)
            typer.secho("  • The project is not shared or is private", fg=typer.colors.YELLOW, err=True)
            typer.secho("  • The project has been deleted", fg=typer.colors.YELLOW, err=True)
            typer.secho("", err=True)
            typer.secho("Note: Only public and shared projects can be downloaded.", fg=typer.colors.CYAN, err=True)
        else:
            typer.secho(f"Error downloading project: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error downloading project: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
