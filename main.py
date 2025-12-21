import re
from pathlib import Path
from typing import Optional

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
            raise ValueError("Could not retrieve project token. The project may be private or not exist.")
        
        # Construct the download URL with token
        download_url = f"https://projects.scratch.mit.edu/{project_id}?token={project_token}"
        
        # Download the project
        typer.echo("Downloading project file...")
        response = requests.get(download_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Determine output filename
        if name:
            filename = f"{name}.sb3"
        else:
            filename = f"{project_id}.sb3"
        
        # Save to file
        output_path = Path(filename)
        output_path.write_bytes(response.content)
        
        typer.secho(f"✓ Successfully downloaded to {filename}", fg=typer.colors.GREEN)
        
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error downloading project: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
