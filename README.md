# Scratch Tool

A command-line tool to download Scratch 3 projects as complete `.sb3` files (ZIP archives containing `project.json` and all assets).

**Note: Only public and shared projects can be downloaded.** Private or unshared projects are not accessible through the Scratch API.

## Features

- Downloads complete Scratch 3 projects with all assets (costumes, sounds, etc.)
- Creates proper `.sb3` files identical to "File > Save to your computer" in Scratch
- Generates HTML documentation with thumbnails and audio players
- Analyzes project structure and displays detailed statistics
- Views project metadata with colorized JSON output
- Supports multiple input formats (URL, project ID, or local file)
- Deduplicates shared assets across sprites
- Progress display during download

## Installation

```bash
pip install -e .
```

## Usage

The tool provides four main commands: `metadata`, `download`, `analyze`, and `document`.

**Important:** Projects must be public and shared on Scratch. Unshared or private projects cannot be accessed.

### Fetch Project Metadata

View detailed information about a Scratch project without downloading it:

```bash
# Using project ID
python main.py metadata 1252755893

# Using full project URL
python main.py metadata https://scratch.mit.edu/projects/1252755893/

# Using editor URL
python main.py metadata https://scratch.mit.edu/projects/1252755893/editor
```

The metadata command displays colorized, pretty-printed JSON with information including:
- Project title, description, and instructions
- Author information
- Project statistics (views, loves, favorites, remixes)
- Creation and modification dates
- Thumbnail URLs
- Project token (for downloading)

### Download Project Files

Download a complete Scratch project as an `.sb3` file, or just the code as JSON:

```bash
# Download full project - file named after project title
python main.py download 1190972813

# Using full project URL
python main.py download https://scratch.mit.edu/projects/1190972813/

# Using editor URL
python main.py download https://scratch.mit.edu/projects/1190972813/editor

# Specify custom output filename (overrides title-based naming)
python main.py download 1190972813 --name my-project

# Download only project.json (code without assets)
python main.py download 1190972813 --code

# Download code with custom name
python main.py download 1190972813 --code --name my-code
```

By default, the downloaded file is named after the project title (e.g., `"▶️ Geometry Dash Wave v19.9018.sb3"`). Invalid filename characters are automatically sanitized. Use the `--name` option to specify a custom filename (without the extension).

**Full Download (.sb3):** The downloaded `.sb3` file is a ZIP archive containing:
- `project.json` - The project structure and code
- All costume and sound assets referenced by the project

**Code Only (--code):** Downloads just the `project.json` file containing:
- All sprites, costumes, and sounds metadata
- All code blocks and scripts
- Variables, lists, and custom blocks
- Stage and sprite properties
- Note: Does not include actual image/sound files

### Analyze Project Structure

Analyze a Scratch project and display detailed statistics. Can analyze from a URL, project ID, or local file:

```bash
# Analyze from project ID
python main.py analyze 1252755893

# Analyze from URL
python main.py analyze https://scratch.mit.edu/projects/1252755893/

# Analyze local project.json file
python main.py analyze sample-project.json

# Validate project.json silently (quiet mode - only shows errors)
python main.py analyze sample-project.json --quiet
```

The analyze command displays comprehensive information including:
- Project overview (Scratch version, VM version)
- Stage information (costumes, sounds, variables, blocks)
- Detailed sprite information (position, size, direction, visibility, assets, blocks)
- Project statistics (total sprites, blocks, variables, lists)
- Extensions used
- Monitors (visible variables)

**Quiet mode** (`--quiet` or `-q`) is useful for validation scripts - it produces no output if the JSON is valid and parseable, but shows errors if validation fails.
- Block types used in the project

### Generate HTML Documentation

Generate comprehensive HTML documentation for a Scratch project with thumbnails and audio players:

```bash
# From project ID
python main.py document 1252755893

# From URL
python main.py document https://scratch.mit.edu/projects/1252755893/

# From local .sb3 file
python main.py document project.sb3

# From local .zip file
python main.py document project.zip

# From directory containing project.json and assets
python main.py document project-directory/

# Specify custom output name (default uses project title or input name)
python main.py document 1252755893 --name custom-doc
```

The document command generates:
- **HTML file** (`<name>.html`) with styled, responsive documentation
- **Assets directory** (`<name>/`) containing all images and sounds

The generated documentation includes:
- Project information (Scratch version, VM version)
- Statistics (sprite count, block count, variables, lists)
- Extensions used
- Stage section with backdrops, sounds, and **scripts**
- Detailed sprite information:
  - Position, size, rotation, visibility
  - Costume gallery with thumbnails
  - Sound list with audio players
  - **Visual script representation** using [scratchblocks](https://scratchblocks.github.io/)
  - Block counts

**Thumbnails:** Image costumes (PNG, JPG, SVG) are automatically converted to 150x150 thumbnails for quick preview.

**Audio Players:** Sound files (WAV, MP3) are embedded with HTML5 audio controls for in-browser playback.

**Script Visualization:** All scripts (code blocks) are rendered using the scratchblocks library, which displays them exactly as they appear in the Scratch editor with proper colors and formatting. Scripts are automatically extracted from the project's block data and converted to scratchblocks notation.

The output HTML is self-contained with embedded CSS and works offline with the assets directory (requires internet connection only for scratchblocks library from CDN).

## Options

### Metadata Command
- `url_or_id`: (Required) Scratch project URL or ID
- `--help`: Show help message

### Download Command
- `url_or_id`: (Required) Scratch project URL or ID
- `--name, -n`: Optional custom output filename (without extension)
- `--code, -c`: Download only project.json instead of full .sb3
- `--help`: Show help message

### Analyze Command
- `source`: (Required) Scratch project URL, ID, or path to project.json file
- `--quiet, -q`: Quiet mode - print nothing if JSON is valid, only show errors (useful for validation)
- `--help`: Show help message

### Document Command
- `source`: (Required) Scratch project URL, ID, .sb3 file, .zip file, or directory
- `--name, -n`: Optional custom output filename and directory name (without extension)
- `--help`: Show help message

## Requirements

- Python 3.11+
- typer
- requests
- pydantic
- pygments
- pillow (for thumbnail generation)
- dominate (for HTML generation)

### Development Dependencies
- pytest
- pytest-mock

## Pydantic Models

The tool includes comprehensive Pydantic models for type-safe parsing and validation:

### API Models (`models/metadata.py`)
- `ProjectMetadata`: Complete project metadata from Scratch API
- `Author`, `Profile`, `History`, `Stats`: User and project statistics
- `ErrorResponse`: API error handling

### Project Models (`models/project.py`)
- `ScratchProject`: Root model for `project.json` files
- `Target`: Sprites and stage with all properties
- `Block`: Code blocks with opcodes, inputs, fields
- `Costume`, `Sound`: Asset definitions
- `Monitor`, `Comment`, `Meta`: Additional project elements

Example usage:

```python
from models.project import ScratchProject

# Parse a downloaded project.json
with open("project.json") as f:
    project = ScratchProject.model_validate_json(f.read())

# Access project structure
print(f"Stage: {project.stage.name}")
print(f"Sprites: {[s.name for s in project.sprites]}")
print(f"Total blocks: {project.count_blocks()}")
print(f"Total sprites: {project.count_sprites()}")

# Get specific sprite
sprite = project.get_sprite("Sprite1")
if sprite:
    print(f"Costumes: {[c.name for c in sprite.costumes]}")
    print(f"Sounds: {[s.name for s in sprite.sounds]}")
```

For a complete project analysis, use the `analyze` command which provides comprehensive statistics and insights.

## Testing

Run the integration tests with pytest:

```bash
# Run all tests
pytest -v

# Run specific test files
pytest test_main.py -v           # CLI command tests
pytest test_project_models.py -v # Pydantic model tests
```

Test coverage:
- 40 CLI integration tests (metadata, download, analyze with quiet mode, parsing, sanitization)
- 9 document command tests (HTML generation, thumbnails, audio players, scratchblocks scripts, multiple input formats)
- 11 Pydantic model validation tests
- Total: 60 tests, all passing

## How It Works

1. Fetches project metadata from Scratch API to get the project token
2. Downloads the `project.json` using the token
3. Extracts all asset references (costumes and sounds) from the JSON
4. Downloads each unique asset from Scratch's CDN
5. Packages everything into a `.sb3` ZIP archive

The tool uses Pydantic models for robust validation of all API responses and project structures, ensuring type safety and data integrity throughout the download process.

