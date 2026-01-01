#!/snap/bin/uv run
#!/home/nbeney/.local/bin/uv run

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests
import typer
from flask import Flask, request, render_template_string, send_file, redirect, url_for
from dominate import document as dom_document
from dominate.tags import (
    a, audio, body, div, h1, h2, h3, head, html, img, li, link, meta, pre, script, source, style, title, ul
)
from dominate.util import raw, text
from PIL import Image
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer
from pydantic import ValidationError

from models.metadata import ErrorResponse, ProjectMetadata
from models.project import ScratchProject
from scratchblocks_converter import target_to_scratchblocks
from server import flask_app

from utils import extract_project_id, extract_project_id_from_filename, sanitize_filename, print_colored_json
from html_docgen import generate_html_documentation

app = typer.Typer()


@app.command()
def metadata(
    url_or_id: str = typer.Argument(..., help="Scratch project URL or ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Custom output filename (without extension)"),
):
    """
    Fetch and save project metadata to a JSON file.
    
    By default, saves to <title>-<project_id>-metadata.json.
    Use --name to specify a custom filename.
    
    Note: Only public and shared projects can be accessed.
    
    Examples:
        scratch-tool metadata https://scratch.mit.edu/projects/1259204833/
        scratch-tool metadata 1259204833
        scratch-tool metadata 1259204833 --name my-project
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
            
            # Generate filename
            if name:
                filename = f"{name}.json"
            else:
                # Sanitize title for filename (remove invalid characters)
                import re
                safe_title = re.sub(r'[<>:"/\\|?*]', '', project_meta.title)
                safe_title = safe_title.strip()
                # Limit length to avoid overly long filenames
                if len(safe_title) > 50:
                    safe_title = safe_title[:50].strip()
                filename = f"{safe_title}-{project_id}-metadata.json"
            
            # Convert to dict with aliases for saving
            output_data = project_meta.model_dump(by_alias=True, mode='json')
            
            # Save to file
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            typer.secho(f"✓ Successfully saved metadata to: {filename}", fg=typer.colors.GREEN)
            typer.echo()
            typer.echo(f"Project: {project_meta.title}")
            typer.echo(f"Author: {project_meta.author.username}")
            typer.echo(f"Views: {project_meta.stats.views:,}")
            typer.echo(f"Loves: {project_meta.stats.loves:,}")
            typer.echo(f"Favorites: {project_meta.stats.favorites:,}")
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
    By default, saves to <title>-<project_id>-project.sb3.
    Use --name to specify a custom filename.
    
    Note: Only public and shared projects can be downloaded.
    
    Examples:
        scratch-tool download https://scratch.mit.edu/projects/1259204833/
        scratch-tool download https://scratch.mit.edu/projects/1259204833/editor
        scratch-tool download 1259204833
        scratch-tool download 1259204833 --name my-project
        scratch-tool download 1259204833 --code
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
                # Use project title and ID, sanitized for filesystem
                safe_title = sanitize_filename(project_metadata.title)
                # Limit title length to avoid overly long filenames
                if len(safe_title) > 50:
                    safe_title = safe_title[:50].strip()
                filename = f"{safe_title}-{project_id}-project.json"
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
            # Use project title and ID, sanitized for filesystem
            safe_title = sanitize_filename(project_metadata.title)
            # Limit title length to avoid overly long filenames
            if len(safe_title) > 50:
                safe_title = safe_title[:50].strip()
            filename = f"{safe_title}-{project_id}-project.sb3"
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
    - Project URL (e.g., https://scratch.mit.edu/projects/1259204833/)
    - Project ID (e.g., 1259204833)
    - Local project.json file (e.g., my-project.json)
    
    Note: When using URL or ID, only public and shared projects can be accessed.
    
    Examples:
        scratch-tool analyze https://scratch.mit.edu/projects/1259204833/
        scratch-tool analyze 1259204833
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
            typer.echo(f"    - Direction: {round(sprite.direction)}°")
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
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Output filename (without .html extension)"),
    standalone: bool = typer.Option(True, "--standalone/--no-standalone", help="Generate single HTML file using Scratch CDN (default: True)"),
):
    """
    Generate HTML documentation for a Scratch project.
    
    Creates an HTML file with project information, sprites, blocks, and assets.
    By default, creates a standalone HTML file linking to Scratch's CDN for assets.
    Use --no-standalone to extract assets locally.
    
    Supported inputs:
    - Project URL (e.g., https://scratch.mit.edu/projects/1259204833/)
    - Project ID (e.g., 1259204833)
    - .sb3 file (e.g., my-project.sb3)
    - .zip file (same format as .sb3)
    - Directory containing project.json and assets
    
    Examples:
        scratch-tool document https://scratch.mit.edu/projects/1259204833/
        scratch-tool document 1259204833
        scratch-tool document my-project.sb3 --name my-docs
        scratch-tool document my-project.sb3 --no-standalone  # Extract assets locally
    """
    try:
        project: ScratchProject
        project_json: dict
        assets_data: dict = {}  # md5ext -> bytes
        output_name: str
        project_id: Optional[str] = None  # Track project ID when available
        project_metadata: Optional[ProjectMetadata] = None  # Track metadata when available from API
        
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
            
            # Try to extract project ID from filename
            project_id = extract_project_id_from_filename(source)
            
            with ZipFile(source_path, 'r') as zf:
                # Read project.json
                project_json = json.loads(zf.read('project.json'))
                project = ScratchProject.model_validate(project_json)
                
                # Read all assets
                for name_in_zip in zf.namelist():
                    if name_in_zip != 'project.json':
                        assets_data[name_in_zip] = zf.read(name_in_zip)
            
            output_name = name if name else source_path.stem
            
        elif source_path.is_file() and source_path.suffix == '.json':
            # Load from .json file (project.json)
            typer.echo(f"Loading project from file: {source}")
            
            # Try to extract project ID from filename
            project_id = extract_project_id_from_filename(source)
            
            with open(source_path) as f:
                project_json = json.load(f)
            project = ScratchProject.model_validate(project_json)
            
            # No assets in standalone JSON file
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
            
            # Only download assets if not in standalone mode
            if not standalone:
                # Collect asset MD5s
                asset_md5s_to_download = set()
                for target in project.targets:
                    for costume in target.costumes:
                        asset_md5s_to_download.add(costume.md5ext)
                    for sound in target.sounds:
                        asset_md5s_to_download.add(sound.md5ext)
                
                typer.echo("Downloading assets...")
                for i, md5ext in enumerate(asset_md5s_to_download, 1):
                    typer.echo(f"  Downloading {i}/{len(asset_md5s_to_download)}: {md5ext}")
                    asset_url = f"https://assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/"
                    try:
                        asset_response = requests.get(asset_url, headers=headers, timeout=30)
                        asset_response.raise_for_status()
                        assets_data[md5ext] = asset_response.content
                    except Exception as e:
                        typer.secho(f"  Warning: Failed to download {md5ext}: {e}", fg=typer.colors.YELLOW)
            
            output_name = name if name else sanitize_filename(project_metadata.title)
        
        # Collect asset MD5s from project (needed for standalone mode)
        asset_md5s = set()
        for target in project.targets:
            for costume in target.costumes:
                asset_md5s.add(costume.md5ext)
            for sound in target.sounds:
                asset_md5s.add(sound.md5ext)
        
        # Apply default naming convention if name wasn't explicitly provided
        # Format: <title>-<project_id>-doc
        if not name and project_id:
            # Get the base title (from metadata or existing output_name)
            if project_metadata:
                base_title = sanitize_filename(project_metadata.title)[:50]
            else:
                # For local files, extract the base title from output_name
                # Remove both "-project" and "-<project_id>" patterns if present
                base_title = output_name
                
                # Remove "-<project_id>-project" pattern (e.g., "Title-123-project" -> "Title")
                import re
                pattern = f'-{project_id}-project$'
                base_title = re.sub(pattern, '', base_title)
                
                # Also handle just "-project" suffix
                if base_title.endswith('-project'):
                    base_title = base_title[:-8]
            
            output_name = f"{base_title}-{project_id}-doc"
        
        # Prepare asset URLs and thumbnails based on mode
        costume_thumbnails = {}
        sound_files = {}
        assets_dir = None
        
        if standalone:
            # Use Scratch CDN for all assets
            typer.echo(f"Creating standalone documentation in {output_name}.html...")
            
            for md5ext in asset_md5s:
                # Link directly to Scratch CDN
                if md5ext.endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    costume_thumbnails[md5ext] = f"https://assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/"
                
                if md5ext.endswith(('.wav', '.mp3')):
                    sound_files[md5ext] = f"https://assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/"
        else:
            # Create output directory for local assets
            assets_dir = Path(output_name)
            assets_dir.mkdir(exist_ok=True)
            
            typer.echo(f"Creating documentation in {output_name}.html and {output_name}/...")
            
            # Save assets and create thumbnails locally
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
        html_content = generate_html_documentation(
            project, project_json, costume_thumbnails, sound_files, output_name, standalone, project_id, project_metadata
        )
        
        # Write HTML file
        html_path = Path(f"{output_name}.html")
        html_path.write_text(html_content, encoding='utf-8')
        
        typer.secho(f"✓ Documentation generated successfully!", fg=typer.colors.GREEN)
        typer.echo(f"  HTML: {html_path}")
        if not standalone and assets_dir:
            typer.echo(f"  Assets: {assets_dir}/")
        elif standalone:
            typer.echo(f"  Mode: Standalone (assets from Scratch CDN)")
        
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@app.command()
def unpack(
    sb3_file: str = typer.Argument(..., help="Path to the .sb3 file to unpack"),
):
    """
    Unpack a Scratch 3 .sb3 file into a directory.
    
    The .sb3 file is a ZIP archive containing project.json and asset files.
    This command:
    1. Creates a directory with the same name as the .sb3 file (without extension)
    2. Extracts all contents from the .sb3 file into that directory
    3. Deletes the original .sb3 file
    
    Examples:
        scratch-tool unpack my-project.sb3
        scratch-tool unpack path/to/project-1259204833-project.sb3
    """
    try:
        # Convert to Path object for easier manipulation
        sb3_path = Path(sb3_file)
        
        # Validate that the file exists
        if not sb3_path.exists():
            typer.secho(f"Error: File not found: {sb3_file}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        
        # Validate that it's a .sb3 file
        if sb3_path.suffix.lower() != '.sb3':
            typer.secho(f"Error: File must have .sb3 extension: {sb3_file}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        
        # Create directory name (same as file name without .sb3 extension)
        output_dir = sb3_path.parent / sb3_path.stem
        
        # Check if directory already exists
        if output_dir.exists():
            typer.secho(f"Error: Directory already exists: {output_dir}", fg=typer.colors.RED, err=True)
            typer.echo("Please remove or rename the existing directory first.")
            raise typer.Exit(1)
        
        typer.echo(f"Unpacking {sb3_path.name}...")
        
        # Step 1: Create the directory
        typer.echo(f"Creating directory: {output_dir.name}/")
        output_dir.mkdir(parents=True, exist_ok=False)
        
        # Step 2: Unzip the .sb3 file into the directory
        typer.echo(f"Extracting contents...")
        try:
            with ZipFile(sb3_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
                extracted_files = zip_ref.namelist()
                typer.echo(f"Extracted {len(extracted_files)} files")
        except Exception as e:
            # If extraction fails, clean up the directory
            typer.secho(f"Error extracting .sb3 file: {e}", fg=typer.colors.RED, err=True)
            if output_dir.exists():
                shutil.rmtree(output_dir)
                typer.echo("Cleaned up incomplete extraction.")
            raise typer.Exit(1)
        
        # Step 3: Delete the original .sb3 file
        typer.echo(f"Deleting original file: {sb3_path.name}")
        sb3_path.unlink()
        
        typer.echo()
        typer.secho("✅ Successfully unpacked!", fg=typer.colors.GREEN)
        typer.echo(f"   Output directory: {output_dir}")
        
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@app.command()
def pack(
    directory: str = typer.Argument(..., help="Path to the directory to pack"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .sb3 filename (without extension)"),
):
    """
    Pack a directory into a Scratch 3 .sb3 file.
    
    The directory should contain project.json and asset files.
    This command:
    1. Validates that the directory exists and contains project.json
    2. Creates a .sb3 file (ZIP archive) with all directory contents
    3. Deletes the original directory after successful packing
    
    By default, the .sb3 file is named after the directory.
    Use --output to specify a custom filename.
    
    Examples:
        scratch-tool pack my-project
        scratch-tool pack path/to/project-1259204833-project
        scratch-tool pack my-project --output custom-name
    """
    try:
        # Convert to Path object for easier manipulation
        dir_path = Path(directory)
        
        # Validate that the directory exists
        if not dir_path.exists():
            typer.secho(f"Error: Directory not found: {directory}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        
        # Validate that it's a directory
        if not dir_path.is_dir():
            typer.secho(f"Error: Not a directory: {directory}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        
        # Validate that project.json exists in the directory
        project_json = dir_path / "project.json"
        if not project_json.exists():
            typer.secho(f"Error: project.json not found in directory: {directory}", fg=typer.colors.RED, err=True)
            typer.echo("The directory must contain a project.json file to be a valid Scratch project.")
            raise typer.Exit(1)
        
        # Determine output filename
        if output:
            sb3_name = output if output.endswith('.sb3') else f"{output}.sb3"
        else:
            sb3_name = f"{dir_path.name}.sb3"
        
        # Create output path in the same parent directory as the input directory
        sb3_path = dir_path.parent / sb3_name
        
        # Check if output file already exists
        if sb3_path.exists():
            typer.secho(f"Error: Output file already exists: {sb3_path}", fg=typer.colors.RED, err=True)
            typer.echo("Please remove or rename the existing file first.")
            raise typer.Exit(1)
        
        typer.echo(f"Packing {dir_path.name}/...")
        
        # Step 1: Create the .sb3 (ZIP) file
        typer.echo(f"Creating archive: {sb3_path.name}")
        try:
            with ZipFile(sb3_path, 'w') as zip_ref:
                # Walk through the directory and add all files
                file_count = 0
                for file_path in dir_path.rglob('*'):
                    if file_path.is_file():
                        # Add file with relative path (relative to the directory being packed)
                        arcname = file_path.relative_to(dir_path)
                        zip_ref.write(file_path, arcname)
                        file_count += 1
                
                typer.echo(f"Packed {file_count} files")
        except Exception as e:
            # If packing fails, clean up the partial .sb3 file
            typer.secho(f"Error creating .sb3 file: {e}", fg=typer.colors.RED, err=True)
            if sb3_path.exists():
                sb3_path.unlink()
                typer.echo("Cleaned up incomplete archive.")
            raise typer.Exit(1)
        
        # Step 2: Delete the original directory
        typer.echo(f"Deleting original directory: {dir_path.name}/")
        shutil.rmtree(dir_path)
        
        typer.echo()
        typer.secho("✅ Successfully packed!", fg=typer.colors.GREEN)
        typer.echo(f"   Output file: {sb3_path}")
        
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@app.command()
def server(
    port: int = typer.Option(5000, "--port", "-p", help="Port to run the server on"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind the server to"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Run server in debug mode"),
):
    """
    Start a web server for documenting Scratch projects.
    
    The server provides a web interface where you can enter a project ID or URL
    and generate HTML documentation.
    
    Routes:
    - / : Home page with input form for project ID/URL
    - /document/<project_id> : Generate and display documentation for a project
    
    Examples:
        scratch-tool server
        scratch-tool server --port 8080
        scratch-tool server --host 0.0.0.0 --port 8080
        scratch-tool server --debug
    """
    # Start the server
    typer.echo(f"Starting Scratch documentation server...")
    typer.echo(f"Server running at: http://{host}:{port}")
    typer.echo(f"Press CTRL+C to stop")
    typer.echo()
    
    try:
        flask_app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        typer.echo("\nServer stopped.")
    except Exception as e:
        typer.secho(f"Error starting server: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


# This allows the app to still run locally with: python main.py
if __name__ == "__main__":
    app()
