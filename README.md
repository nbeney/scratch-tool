# Scratch Tool

A command-line tool to download Scratch 3 projects.

## Installation

```bash
pip install -e .
```

## Usage

Download a Scratch project by providing its URL or project ID:

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

## Options

- `url_or_id`: (Required) Scratch project URL or ID
- `--name, -n`: Optional custom output filename (without extension)
- `--help`: Show help message

## Requirements

- Python 3.11+
- typer
- requests
