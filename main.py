#!/home/nbeney/.local/bin/uv run

import json
import re
import shutil
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests
import typer
from dominate import document as dom_document
from dominate.tags import (
    audio, body, div, h1, h2, h3, head, html, img, meta, source, style, title
)
from PIL import Image
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer
from pydantic import ValidationError

from models.metadata import ErrorResponse, ProjectMetadata
from models.project import ScratchProject

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
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Output filename (without extension)"),
    code: bool = typer.Option(False, "--code", "-c", help="Download only project.json (code) instead of full .sb3")
):
    """
    Download a Scratch 3 project given its URL or ID.
    
    By default, downloads the complete .sb3 file with all assets.
    Use --code to download only the project.json file.
    By default, the file is named after the project title.
    Use --name to specify a custom filename.
    
    Note: Only public and shared projects can be downloaded.
    
    Examples:
        scratch-tool download https://scratch.mit.edu/projects/1252755893/
        scratch-tool download https://scratch.mit.edu/projects/1252755893/editor
        scratch-tool download 1252755893
        scratch-tool download 1252755893 --name my-project
        scratch-tool download 1252755893 --code
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
        
        # If --code flag is set, save only project.json and exit
        if code:
            # Determine output filename for JSON
            if name:
                # User provided custom name
                filename = f"{name}.json"
            else:
                # Use project title, sanitized for filesystem
                safe_title = sanitize_filename(project_metadata.title)
                filename = f"{safe_title}.json"
                typer.echo(f"Using filename: {filename}")
            
            # Write JSON file
            output_path = Path(filename)
            output_path.write_text(json.dumps(project_json, indent=2))
            
            typer.secho(f"✓ Successfully downloaded code to {filename}", fg=typer.colors.GREEN)
            return
        
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


@app.command()
def analyze(
    source: str = typer.Argument(..., help="Scratch project URL, ID, or path to project.json file"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode: print nothing if JSON is valid, only show errors"),
):
    """
    Analyze a Scratch project and display detailed statistics.
    
    Can analyze from:
    - Project URL (e.g., https://scratch.mit.edu/projects/1252755893/)
    - Project ID (e.g., 1252755893)
    - Local project.json file (e.g., my-project.json)
    
    Note: When using URL or ID, only public and shared projects can be accessed.
    
    Examples:
        scratch-tool analyze https://scratch.mit.edu/projects/1252755893/
        scratch-tool analyze 1252755893
        scratch-tool analyze sample-project.json
        scratch-tool analyze sample-project.json --quiet  # Validate silently
    """
    try:
        project: ScratchProject
        source_name: str
        
        # Check if source is a local file
        file_path = Path(source)
        if file_path.exists() and file_path.is_file():
            # Load from local file
            if not quiet:
                typer.echo(f"Loading project from file: {file_path.name}")
                typer.echo("=" * 60)
            
            with open(file_path) as f:
                project = ScratchProject.model_validate_json(f.read())
            source_name = file_path.name
        else:
            # Try to extract project ID and download from Scratch
            project_id = extract_project_id(source)
            if not quiet:
                typer.echo(f"Fetching project {project_id} from Scratch...")
                typer.echo("=" * 60)
            
            # Get metadata
            api_url = f"https://api.scratch.mit.edu/projects/{project_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            metadata_response = requests.get(api_url, headers=headers, timeout=30)
            metadata_response.raise_for_status()
            metadata_dict = metadata_response.json()
            
            # Validate metadata
            try:
                project_metadata = ProjectMetadata.model_validate(metadata_dict)
            except ValidationError:
                try:
                    error = ErrorResponse.model_validate(metadata_dict)
                    raise ValueError(f"API Error: {error.code}. The project may be private, unshared, or deleted.")
                except ValidationError:
                    raise ValueError("Could not parse project metadata.")
            
            # Download project.json
            download_url = f"https://projects.scratch.mit.edu/{project_id}?token={project_metadata.project_token}"
            response = requests.get(download_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            project = ScratchProject.model_validate(response.json())
            source_name = f"{project_metadata.title} (ID: {project_id})"
        
        # If quiet mode, just exit successfully (JSON is valid)
        if quiet:
            return
        
        # Basic project info
        typer.echo(f"\n📊 Project Overview:")
        typer.echo(f"  Semver: {project.meta.semver}")
        typer.echo(f"  VM: {project.meta.vm}")
        typer.echo(f"  User Agent: {project.meta.agent or 'N/A'}")
        
        # Stage information
        stage = project.stage
        typer.echo(f"\n🎭 Stage:")
        typer.echo(f"  Name: {stage.name}")
        typer.echo(f"  Costumes: {len(stage.costumes)}")
        typer.echo(f"  Sounds: {len(stage.sounds)}")
        typer.echo(f"  Variables: {len(stage.variables)}")
        typer.echo(f"  Lists: {len(stage.lists)}")
        typer.echo(f"  Blocks: {len(stage.blocks)}")
        
        # Sprites
        sprites = project.sprites
        typer.echo(f"\n🎮 Sprites ({len(sprites)}):")
        for sprite in sprites:
            typer.echo(f"  • {sprite.name}")
            typer.echo(f"    - Position: ({sprite.x}, {sprite.y})")
            typer.echo(f"    - Size: {sprite.size}%")
            typer.echo(f"    - Direction: {sprite.direction}°")
            typer.echo(f"    - Visible: {sprite.visible}")
            typer.echo(f"    - Costumes: {len(sprite.costumes)}")
            typer.echo(f"    - Sounds: {len(sprite.sounds)}")
            typer.echo(f"    - Blocks: {len(sprite.blocks)}")
        
        # Statistics
        typer.echo(f"\n📈 Statistics:")
        typer.echo(f"  Total Sprites: {project.count_sprites()}")
        typer.echo(f"  Total Blocks: {project.count_blocks()}")
        typer.echo(f"  Total Variables: {len(project.get_all_variables())}")
        typer.echo(f"  Total Lists: {len(project.get_all_lists())}")
        
        # Extensions
        if project.extensions:
            typer.echo(f"\n🔌 Extensions:")
            for ext in project.extensions:
                typer.echo(f"  • {ext}")
        
        # Monitors
        if project.monitors:
            typer.echo(f"\n👁️  Monitors ({len(project.monitors)}):")
            for monitor in project.monitors:
                typer.echo(f"  • {monitor.params.get('VARIABLE', 'Unknown')} ({monitor.mode})")
        
        # Block types used
        block_types = set()
        for target in project.targets:
            for block in target.blocks.values():
                block_types.add(block.opcode)
        
        typer.echo(f"\n🧩 Block Types Used ({len(block_types)}):")
        # Show first 10 block types
        for block_type in sorted(block_types)[:10]:
            typer.echo(f"  • {block_type}")
        if len(block_types) > 10:
            typer.echo(f"  ... and {len(block_types) - 10} more")
        
        typer.echo("\n" + "=" * 60)
        typer.secho("✅ Analysis complete!", fg=typer.colors.GREEN)
        
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
            typer.secho(f"Error fetching project: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except ValidationError as e:
        typer.secho(f"Error parsing project data: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@app.command()
def document(
    source: str = typer.Argument(..., help="Scratch project URL, ID, .sb3 file, .zip file, or directory with project.json"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Output filename (without .html extension) and directory name"),
):
    """
    Generate HTML documentation for a Scratch project.
    
    Creates an HTML file with project information, sprites, blocks, and assets.
    Also creates a directory with extracted costume images (thumbnails) and sound files.
    
    Supported inputs:
    - Project URL (e.g., https://scratch.mit.edu/projects/1252755893/)
    - Project ID (e.g., 1252755893)
    - .sb3 file (e.g., my-project.sb3)
    - .zip file (same format as .sb3)
    - Directory containing project.json and assets
    
    Examples:
        scratch-tool document https://scratch.mit.edu/projects/1252755893/
        scratch-tool document 1252755893
        scratch-tool document my-project.sb3
        scratch-tool document project-directory/
        scratch-tool document my-project.sb3 --name my-docs
    """
    try:
        project: ScratchProject
        project_json: dict
        assets_data: dict = {}  # md5ext -> bytes
        output_name: str
        
        # Determine source type and load project
        source_path = Path(source)
        
        if source_path.is_dir():
            # Load from directory
            typer.echo(f"Loading project from directory: {source}")
            project_json_path = source_path / "project.json"
            if not project_json_path.exists():
                raise ValueError(f"No project.json found in directory: {source}")
            
            with open(project_json_path) as f:
                project_json = json.load(f)
            project = ScratchProject.model_validate(project_json)
            
            # Load assets from directory
            for file_path in source_path.iterdir():
                if file_path.is_file() and file_path.name != "project.json":
                    assets_data[file_path.name] = file_path.read_bytes()
            
            output_name = name if name else source_path.name
            
        elif source_path.is_file() and source_path.suffix in ['.sb3', '.zip']:
            # Load from .sb3 or .zip file
            typer.echo(f"Loading project from file: {source}")
            
            with ZipFile(source_path, 'r') as zf:
                # Read project.json
                project_json = json.loads(zf.read('project.json'))
                project = ScratchProject.model_validate(project_json)
                
                # Read all assets
                for name_in_zip in zf.namelist():
                    if name_in_zip != 'project.json':
                        assets_data[name_in_zip] = zf.read(name_in_zip)
            
            output_name = name if name else source_path.stem
            
        else:
            # Try as URL or project ID
            project_id = extract_project_id(source)
            typer.echo(f"Downloading project {project_id} from Scratch...")
            
            # Get metadata for title
            api_url = f"https://api.scratch.mit.edu/projects/{project_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            metadata_response = requests.get(api_url, headers=headers, timeout=30)
            metadata_response.raise_for_status()
            metadata_dict = metadata_response.json()
            
            try:
                project_metadata = ProjectMetadata.model_validate(metadata_dict)
            except ValidationError:
                raise ValueError("Could not parse project metadata.")
            
            # Download project.json
            download_url = f"https://projects.scratch.mit.edu/{project_id}?token={project_metadata.project_token}"
            response = requests.get(download_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            project_json = response.json()
            project = ScratchProject.model_validate(project_json)
            
            # Download all assets
            typer.echo("Downloading assets...")
            asset_md5s = set()
            for target in project.targets:
                for costume in target.costumes:
                    asset_md5s.add(costume.md5ext)
                for sound in target.sounds:
                    asset_md5s.add(sound.md5ext)
            
            for i, md5ext in enumerate(asset_md5s, 1):
                typer.echo(f"  Downloading {i}/{len(asset_md5s)}: {md5ext}")
                asset_url = f"https://assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/"
                try:
                    asset_response = requests.get(asset_url, headers=headers, timeout=30)
                    asset_response.raise_for_status()
                    assets_data[md5ext] = asset_response.content
                except Exception as e:
                    typer.secho(f"  Warning: Failed to download {md5ext}: {e}", fg=typer.colors.YELLOW)
            
            output_name = name if name else sanitize_filename(project_metadata.title)
        
        # Create output directory for assets
        assets_dir = Path(output_name)
        assets_dir.mkdir(exist_ok=True)
        
        typer.echo(f"Creating documentation in {output_name}.html and {output_name}/...")
        
        # Save assets and create thumbnails
        costume_thumbnails = {}
        sound_files = {}
        
        for md5ext, data in assets_data.items():
            asset_path = assets_dir / md5ext
            asset_path.write_bytes(data)
            
            # Create thumbnails for images
            if md5ext.endswith(('.png', '.jpg', '.jpeg', '.svg')):
                if md5ext.endswith('.svg'):
                    # SVGs can be used directly
                    costume_thumbnails[md5ext] = md5ext
                else:
                    # Create thumbnail for bitmap images
                    try:
                        img = Image.open(asset_path)
                        # Create thumbnail (max 150x150)
                        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                        thumb_name = f"thumb_{md5ext}"
                        thumb_path = assets_dir / thumb_name
                        img.save(thumb_path)
                        costume_thumbnails[md5ext] = thumb_name
                    except Exception as e:
                        typer.secho(f"  Warning: Could not create thumbnail for {md5ext}: {e}", fg=typer.colors.YELLOW)
                        costume_thumbnails[md5ext] = md5ext
            
            # Track sound files
            if md5ext.endswith(('.wav', '.mp3')):
                sound_files[md5ext] = md5ext
        
        # Generate HTML documentation
        html_content = generate_html_documentation(project, project_json, costume_thumbnails, sound_files, output_name)
        
        # Write HTML file
        html_path = Path(f"{output_name}.html")
        html_path.write_text(html_content, encoding='utf-8')
        
        typer.secho(f"✓ Documentation generated successfully!", fg=typer.colors.GREEN)
        typer.echo(f"  HTML: {html_path}")
        typer.echo(f"  Assets: {assets_dir}/")
        
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


def generate_html_documentation(
    project: ScratchProject,
    project_json: dict,
    costume_thumbnails: dict,
    sound_files: dict,
    output_name: str
) -> str:
    """Generate HTML documentation for a Scratch project using dominate."""
    
    doc = dom_document(title='Scratch Project Documentation')
    
    with doc.head:
        meta(charset='UTF-8')
        meta(name='viewport', content='width=device-width, initial-scale=1.0')
        
        # CSS styles
        style("""
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1, h2, h3 {
            color: #ff6680;
        }
        .section {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .metadata-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .metadata-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }
        .sprite {
            border: 2px solid #ddd;
            padding: 15px;
            margin: 15px 0;
            border-radius: 8px;
            background: #fafafa;
        }
        .sprite-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        .sprite-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #4a90e2;
        }
        .sprite-props {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 10px 0;
        }
        .prop {
            background: white;
            padding: 8px;
            border-radius: 4px;
            border-left: 3px solid #4a90e2;
        }
        .prop-label {
            font-size: 0.85em;
            color: #666;
        }
        .prop-value {
            font-weight: bold;
            color: #333;
        }
        .assets {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 15px 0;
        }
        .asset {
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .asset img {
            max-width: 150px;
            max-height: 150px;
            display: block;
            margin: 0 auto 10px;
            border: 1px solid #eee;
        }
        .asset-name {
            font-size: 0.9em;
            color: #333;
            word-break: break-word;
        }
        .audio-player {
            margin-top: 10px;
        }
        .blocks-count {
            background: #e8f4fd;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            border-left: 4px solid #4a90e2;
        }
        .extensions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .extension {
            background: #fef3cd;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            border: 1px solid #f5c842;
        }
        .statistics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 1em;
            opacity: 0.9;
        }
        """)
    
    with doc:
        h1('🎨 Scratch Project Documentation')
        
        # Project Information Section
        with div(cls='section'):
            h2('Project Information')
            with div(cls='metadata'):
                with div(cls='metadata-item'):
                    div('Scratch Version', cls='metadata-label')
                    div(project.meta.semver)
                with div(cls='metadata-item'):
                    div('VM Version', cls='metadata-label')
                    div(project.meta.vm)
        
        # Statistics Section
        with div(cls='section'):
            h2('Statistics')
            with div(cls='statistics'):
                with div(cls='stat-card'):
                    div('Sprites', cls='stat-label')
                    div(str(project.count_sprites()), cls='stat-value')
                with div(cls='stat-card'):
                    div('Total Blocks', cls='stat-label')
                    div(str(project.count_blocks()), cls='stat-value')
                with div(cls='stat-card'):
                    div('Variables', cls='stat-label')
                    div(str(len(project.get_all_variables())), cls='stat-value')
                with div(cls='stat-card'):
                    div('Lists', cls='stat-label')
                    div(str(len(project.get_all_lists())), cls='stat-value')
        
        # Extensions Section
        if project.extensions:
            with div(cls='section'):
                h2('Extensions Used')
                with div(cls='extensions'):
                    for ext in project.extensions:
                        div(f'🔌 {ext}', cls='extension')
        
        # Stage Section
        stage = project.stage
        if stage:
            with div(cls='section'):
                h2('🎭 Stage')
                with div(cls='sprite'):
                    with div(cls='sprite-header'):
                        div(stage.name, cls='sprite-name')
                    
                    with div(cls='sprite-props'):
                        with div(cls='prop'):
                            div('Costumes', cls='prop-label')
                            div(str(len(stage.costumes)), cls='prop-value')
                        with div(cls='prop'):
                            div('Sounds', cls='prop-label')
                            div(str(len(stage.sounds)), cls='prop-value')
                        with div(cls='prop'):
                            div('Variables', cls='prop-label')
                            div(str(len(stage.variables)), cls='prop-value')
                        with div(cls='prop'):
                            div('Lists', cls='prop-label')
                            div(str(len(stage.lists)), cls='prop-value')
                        with div(cls='prop'):
                            div('Blocks', cls='prop-label')
                            div(str(len(stage.blocks)), cls='prop-value')
                    
                    # Stage costumes (backdrops)
                    if stage.costumes:
                        h3('Backdrops')
                        with div(cls='assets'):
                            for costume in stage.costumes:
                                thumb = costume_thumbnails.get(costume.md5ext, '')
                                if thumb:
                                    with div(cls='asset'):
                                        img(src=f'{output_name}/{thumb}', alt=costume.name)
                                        div(costume.name, cls='asset-name')
                    
                    # Stage sounds
                    if stage.sounds:
                        h3('Sounds')
                        with div(cls='assets'):
                            for sound in stage.sounds:
                                if sound.md5ext in sound_files:
                                    with div(cls='asset'):
                                        div(f'🔊 {sound.name}', cls='asset-name')
                                        with audio(controls=True, cls='audio-player'):
                                            source(src=f'{output_name}/{sound.md5ext}', 
                                                  type=f'audio/{sound.dataFormat}')
        
        # Sprites Section
        sprites = project.sprites
        if sprites:
            with div(cls='section'):
                h2('🎮 Sprites')
                for sprite in sprites:
                    with div(cls='sprite'):
                        with div(cls='sprite-header'):
                            div(sprite.name, cls='sprite-name')
                        
                        with div(cls='sprite-props'):
                            with div(cls='prop'):
                                div('Position', cls='prop-label')
                                div(f'({sprite.x}, {sprite.y})', cls='prop-value')
                            with div(cls='prop'):
                                div('Size', cls='prop-label')
                                div(f'{sprite.size}%', cls='prop-value')
                            with div(cls='prop'):
                                div('Direction', cls='prop-label')
                                div(f'{sprite.direction}°', cls='prop-value')
                            with div(cls='prop'):
                                div('Visible', cls='prop-label')
                                div('Yes' if sprite.visible else 'No', cls='prop-value')
                            with div(cls='prop'):
                                div('Rotation Style', cls='prop-label')
                                div(sprite.rotationStyle or 'all around', cls='prop-value')
                        
                        with div(cls='blocks-count'):
                            div(f'📦 {len(sprite.blocks)} blocks | '
                                f'🎨 {len(sprite.costumes)} costumes | '
                                f'🔊 {len(sprite.sounds)} sounds', escape=False)
                        
                        # Sprite costumes
                        if sprite.costumes:
                            h3('Costumes')
                            with div(cls='assets'):
                                for costume in sprite.costumes:
                                    thumb = costume_thumbnails.get(costume.md5ext, '')
                                    if thumb:
                                        with div(cls='asset'):
                                            img(src=f'{output_name}/{thumb}', alt=costume.name)
                                            div(costume.name, cls='asset-name')
                        
                        # Sprite sounds
                        if sprite.sounds:
                            h3('Sounds')
                            with div(cls='assets'):
                                for sound in sprite.sounds:
                                    if sound.md5ext in sound_files:
                                        with div(cls='asset'):
                                            div(f'🔊 {sound.name}', cls='asset-name')
                                            with audio(controls=True, cls='audio-player'):
                                                source(src=f'{output_name}/{sound.md5ext}', 
                                                      type=f'audio/{sound.dataFormat}')
    
    return str(doc)


if __name__ == "__main__":
    app()
