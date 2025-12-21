# Scratch Tool

A command-line tool to download Scratch 3 projects as complete `.sb3` files (ZIP archives containing `project.json` and all assets).

**Note: Only public and shared projects can be downloaded.** Private or unshared projects are not accessible through the Scratch API.

## Features

- Downloads complete Scratch 3 projects with all assets (costumes, sounds, etc.)
- Creates proper `.sb3` files identical to "File > Save to your computer" in Scratch
- Supports multiple input formats (URL or project ID)
- Deduplicates shared assets across sprites
- Progress display during download

## Installation

```bash
pip install -e .
```

## Usage

The tool provides two main commands: `metadata` and `download`.

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

## Options

### Metadata Command
- `url_or_id`: (Required) Scratch project URL or ID
- `--help`: Show help message

### Download Command
- `url_or_id`: (Required) Scratch project URL or ID
- `--name, -n`: Optional custom output filename (without extension)
- `--code, -c`: Download only project.json instead of full .sb3
- `--help`: Show help message

## Requirements

- Python 3.11+
- typer
- requests
- pydantic
- pygments

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

See `example_usage.py` for a complete project analysis script that demonstrates all model features.

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
- 25 CLI integration tests (metadata, download, parsing, sanitization)
- 11 Pydantic model validation tests
- Total: 36 tests, all passing

## How It Works

1. Fetches project metadata from Scratch API to get the project token
2. Downloads the `project.json` using the token
3. Extracts all asset references (costumes and sounds) from the JSON
4. Downloads each unique asset from Scratch's CDN
5. Packages everything into a `.sb3` ZIP archive

The tool uses Pydantic models for robust validation of all API responses and project structures, ensuring type safety and data integrity throughout the download process.

