#!/home/nbeney/.local/bin/uv run

import json
import re
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests
import typer

app = typer.Typer()


def extract_project_id(url_or_id: str) -> str:
    """Extract project ID from URL or return the ID if already a number."""
    # If it's already just a number, return it
    if url_or_id.isdigit():
        return url_or_id
    
    # Try to extract ID from URL patterns
    # Matches: https://scratch.mit.edu/projects/1190972813/
    # Matches: https://scratch.mit.edu/projects/1190972813/editor
    pattern = r'scratch\.mit\.edu/projects/(\d+)'
    match = re.search(pattern, url_or_id)
    
    if match:
        return match.group(1)
    
    # If no match found, raise an error
    raise ValueError(f"Could not extract project ID from: {url_or_id}")


@app.command()
def download(
    url_or_id: str = typer.Argument(..., help="Scratch project URL or ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Output filename (without extension)")
):
    """
    Download a Scratch 3 project given its URL or ID.
    
    Note: Only public and shared projects can be downloaded.
    
    Examples:
        scratch-tool download https://scratch.mit.edu/projects/1190972813/
        scratch-tool download https://scratch.mit.edu/projects/1190972813/editor
        scratch-tool download 1190972813
        scratch-tool download 1190972813 --name my-project
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
        metadata = metadata_response.json()
        
        # Get the project token
        project_token = metadata.get('project_token')
        if not project_token:
            raise ValueError("Could not retrieve project token. The project may be private or unshared. Only public and shared projects can be downloaded.")
        
        # Construct the download URL with token
        download_url = f"https://projects.scratch.mit.edu/{project_id}?token={project_token}"
        
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
            filename = f"{name}.sb3"
        else:
            filename = f"{project_id}.sb3"
        
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
