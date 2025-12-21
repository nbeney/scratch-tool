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

Download a complete Scratch project as an `.sb3` file:

```bash
# Using project ID
python main.py 1190972813

# Using full project URL
python main.py https://scratch.mit.edu/projects/1190972813/

# Using editor URL
python main.py https://scratch.mit.edu/projects/1190972813/editor

# Specify custom output filename
python main.py 1190972813 --name my-project
```

By default, the project is saved as `{project_id}.sb3`. Use the `--name` option to specify a custom filename (without the .sb3 extension).

The downloaded `.sb3` file is a ZIP archive containing:
- `project.json` - The project structure and code
- All costume and sound assets referenced by the project

## Options

### Metadata Command
- `url_or_id`: (Required) Scratch project URL or ID
- `--help`: Show help message

### Download Command
- `url_or_id`: (Required) Scratch project URL or ID
- `--name, -n`: Optional custom output filename (without extension)
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

## Testing

Run the integration tests with pytest:

```bash
pytest test_main.py -v
```

## How It Works

1. Fetches project metadata from Scratch API to get the project token
2. Downloads the `project.json` using the token
3. Extracts all asset references (costumes and sounds) from the JSON
4. Downloads each unique asset from Scratch's CDN
5. Packages everything into a `.sb3` ZIP archive

