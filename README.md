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

The tool provides six main commands: `metadata`, `download`, `analyze`, `document`, `unpack`, and `pack`.

**Important:** Projects must be public and shared on Scratch. Unshared or private projects cannot be accessed.

### Fetch Project Metadata

View detailed information about a Scratch project without downloading it:

```bash
# Using project ID
python main.py metadata 1259204833

# Using full project URL
python main.py metadata https://scratch.mit.edu/projects/1259204833/

# Using editor URL
python main.py metadata https://scratch.mit.edu/projects/1259204833/editor
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
python main.py analyze 1259204833

# Analyze from URL
python main.py analyze https://scratch.mit.edu/projects/1259204833/

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
# From project ID (standalone mode - single HTML file)
python main.py document 1259204833

# From URL
python main.py document https://scratch.mit.edu/projects/1259204833/

# From local .sb3 file
python main.py document project.sb3

# From local .zip file
python main.py document project.zip

# From directory containing project.json and assets
python main.py document project-directory/

# Specify custom output name (default uses project title or input name)
python main.py document 1259204833 --name custom-doc

# Generate with local assets directory (instead of using CDN)
python main.py document 1259204833 --no-standalone
```

#### Output Modes

**Standalone Mode (default):** Generates a single, portable HTML file that links to assets from the Scratch CDN:
- **HTML file** (`<name>.html`) - single file with all documentation
- **No assets directory** - images and sounds are linked from `https://assets.scratch.mit.edu/`
- **Smaller output** - no local copies of assets
- **Requires internet** - assets load from CDN when viewing HTML
- **Easy sharing** - just one file to distribute

**Local Mode (`--no-standalone`):** Generates HTML with a local assets directory:
- **HTML file** (`<name>.html`) - documentation with local asset references
- **Assets directory** (`<name>/`) - contains all images and sounds
- **Larger output** - local copies of all assets
- **Works offline** - all assets bundled locally (still needs CDN for scratchblocks library)
- **Thumbnails** - PNG/JPG costumes get 150x150 thumbnail previews

The generated documentation includes:
- Project information (Scratch version, VM version)
- Statistics (sprite count, block count, variables, lists)
- Extensions used
- Stage section with backdrops, sounds, and **scripts**
- Detailed sprite information:
  - Position, size, rotation, visibility
  - Costume gallery with thumbnails (standalone: full images; local: 150x150 thumbnails)
  - Sound list with audio players
  - **Visual script representation** using [scratchblocks](https://scratchblocks.github.io/)
  - Block counts

**Script Visualization:** All scripts (code blocks) are rendered using the scratchblocks library, which displays them exactly as they appear in the Scratch editor with proper colors and formatting. Scripts are automatically extracted from the project's block data and converted to scratchblocks notation.

The output HTML is self-contained with embedded CSS. In standalone mode, requires internet for both assets and scratchblocks. In local mode, only scratchblocks requires internet.

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
- `--standalone/--no-standalone`: Generate standalone HTML with CDN links (default: `--standalone`) or local HTML with assets directory (`--no-standalone`)
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

### Unpack Project Files

Extract the contents of a `.sb3` file into a directory for inspection or editing:

```bash
# Unpack a downloaded project
python main.py unpack my-project.sb3

# Result:
# - Creates directory: my-project/
# - Extracts: project.json and all asset files (SVG, PNG, WAV, MP3)
# - Deletes: my-project.sb3 (original file removed after successful extraction)

# Example with full workflow
python main.py download 1259204833
python main.py unpack "All Blocks-1259204833-project.sb3"
ls "All Blocks-1259204833-project/"  # View extracted files
```

The `unpack` command:
- Creates a directory with the same name as the .sb3 file (without extension)
- Extracts all contents (project.json and asset files) into that directory
- Deletes the original .sb3 file after successful extraction
- Provides error handling for existing directories and invalid files

**Use cases:**
- Inspect project structure and JSON format
- Extract assets (images, sounds) for reuse
- Manually edit project.json for advanced modifications
- Store unpacked projects in version control systems

**Note:** To repack a directory back into an .sb3 file, use: `cd my-project && zip -r ../my-project.sb3 *`

See [UNPACK_COMMAND.md](UNPACK_COMMAND.md) for detailed documentation and examples.

### Pack Project Files

Pack a directory back into a `.sb3` file (reverse of unpack):

```bash
# Pack a directory into an .sb3 file
python main.py pack my-project

# Result:
# - Creates file: my-project.sb3 (ZIP archive with all contents)
# - Deletes: my-project/ directory (removed after successful packing)

# Pack with custom output name
python main.py pack my-project --output custom-name
# Creates: custom-name.sb3

# Complete roundtrip example (unpack → edit → pack)
python main.py download 1259204833
python main.py unpack "All Blocks-1259204833-project.sb3"
# Edit files in "All Blocks-1259204833-project/" directory
python main.py pack "All Blocks-1259204833-project"
# Back to "All Blocks-1259204833-project.sb3"
```

The `pack` command:
- Validates that the directory exists and contains project.json
- Creates a .sb3 file (ZIP archive) with all directory contents
- Deletes the original directory after successful packing
- Provides error handling for missing files and existing output files

**Use cases:**
- Repack projects after manual editing
- Create .sb3 files from extracted/modified projects
- Roundtrip workflow: download → unpack → edit → pack → upload to Scratch
- Version control: commit unpacked changes, then pack for distribution

**Note:** The `pack` and `unpack` commands are inverse operations. Running unpack followed by pack (or vice versa) recreates a valid .sb3 file.

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
- 4 unpack command tests (extraction, error handling, directory conflicts)
- 7 pack command tests (packing, custom output, error handling, roundtrip validation)
- 11 Pydantic model validation tests
- Total: 79 tests, all passing

## How It Works

1. Fetches project metadata from Scratch API to get the project token
2. Downloads the `project.json` using the token
3. Extracts all asset references (costumes and sounds) from the JSON
4. Downloads each unique asset from Scratch's CDN
5. Packages everything into a `.sb3` ZIP archive

The tool uses Pydantic models for robust validation of all API responses and project structures, ensuring type safety and data integrity throughout the download process.

