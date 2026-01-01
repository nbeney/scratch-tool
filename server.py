from flask import Flask, request, render_template_string, redirect, url_for, Response
from flask import request, render_template_string
from flask import request, redirect, url_for
from flask import Response, redirect, url_for

import requests
import typer

from pydantic import ValidationError
from utils import extract_project_id, extract_project_id_from_filename, sanitize_filename, print_colored_json
from html_docgen import generate_html_documentation
from models.metadata import ErrorResponse, ProjectMetadata
from models.project import ScratchProject
from scratchblocks_converter import target_to_scratchblocks

# Create Flask app instance for WSGI
flask_app = Flask(__name__)

# HTML template for the home page
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scratch Project Documenter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            color: #555;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .examples {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .examples h3 {
            color: #555;
            margin-bottom: 10px;
            font-size: 1.2em;
        }
        
        .examples ul {
            list-style: none;
            color: #666;
        }
        
        .examples li {
            margin: 8px 0;
            padding-left: 20px;
            position: relative;
        }
        
        .examples li:before {
            content: "→";
            position: absolute;
            left: 0;
            color: #667eea;
        }
        
        .error {
            background: #fee;
            border: 1px solid #fcc;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            color: #c33;
        }
        
        .footer {
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Scratch Documenter</h1>
        <p class="subtitle">Generate beautiful HTML documentation for any Scratch project</p>
        
        {% if error %}
        <div class="error">
            <strong>Error:</strong> {{ error }}
        </div>
        {% endif %}
        
        <form method="POST" action="/generate">
            <div class="form-group">
                <label for="project_input">Project ID or URL</label>
                <input 
                    type="text" 
                    id="project_input" 
                    name="project_input" 
                    placeholder="1259204833 or https://scratch.mit.edu/projects/1259204833/"
                    required
                    autofocus
                >
            </div>
            
            <button type="submit">📄 Generate Documentation</button>
        </form>
        
        <div class="examples">
            <h3>Example Inputs:</h3>
            <ul>
                <li>Project ID: <code>1259204833</code></li>
                <li>Full URL: <code>https://scratch.mit.edu/projects/1259204833/</code></li>
                <li>Editor URL: <code>https://scratch.mit.edu/projects/1259204833/editor</code></li>
            </ul>
        </div>
        
        <div class="footer">
            © 2026 by Nicolas Beney - licensed under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>
        </div>
    </div>
</body>
</html>
"""

@flask_app.route("/")
def home():
    """Home page with input form."""
    error = request.args.get('error')
    return render_template_string(HOME_TEMPLATE, error=error)

@flask_app.route("/generate", methods=["POST"])
def generate():
    """Handle form submission and redirect to documentation page."""
    project_input = request.form.get("project_input", "").strip()
    
    if not project_input:
        return redirect(url_for('home', error="Please enter a project ID or URL"))
    
    try:
        # Extract project ID from URL or use ID directly
        project_id = extract_project_id(project_input)
        return redirect(url_for('document_project', project_id=project_id))
    except ValueError as e:
        return redirect(url_for('home', error=str(e)))

@flask_app.route("/document/<project_id>")
def document_project(project_id: str):
    """Generate and display documentation for a project."""
    try:
        typer.echo(f"Generating documentation for project {project_id}...")
        
        # Fetch project metadata
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
            # Not valid metadata, might be error response
            try:
                error_resp = ErrorResponse.model_validate(metadata_dict)
                error_msg = f"Scratch API Error: {error_resp.message}"
                return redirect(url_for('home', error=error_msg))
            except ValidationError:
                return redirect(url_for('home', error="Could not parse Scratch API response"))
        
        # Download project.json
        project_token = project_metadata.project_token
        project_url = f"https://projects.scratch.mit.edu/{project_id}?token={project_token}"
        
        project_response = requests.get(project_url, headers=headers, timeout=30)
        project_response.raise_for_status()
        project_data = project_response.json()
        
        # Parse project
        try:
            project = ScratchProject.model_validate(project_data)
        except ValidationError as e:
            return redirect(url_for('home', error=f"Invalid project format: {str(e)}"))
        
        # In standalone mode (using CDN), we don't need to download assets
        # Just map md5ext to Scratch CDN URLs
        costume_thumbnails = {}
        sound_files = {}
        
        # Map all costumes to CDN URLs
        for target in project.targets:
            for costume in target.costumes:
                # Use Scratch CDN URL for images
                costume_thumbnails[costume.md5ext] = f"https://assets.scratch.mit.edu/internalapi/asset/{costume.md5ext}/get/"
            
            for sound in target.sounds:
                # Use Scratch CDN URL for sounds
                sound_files[sound.md5ext] = f"https://assets.scratch.mit.edu/internalapi/asset/{sound.md5ext}/get/"
        
        # Generate HTML using standalone mode (CDN links)
        html_content = generate_html_documentation(
            project=project,
            project_json=project_data,
            costume_thumbnails=costume_thumbnails,
            sound_files=sound_files,
            output_name=project_metadata.title,
            standalone=True,  # Always use standalone mode for web server
            project_id=project_id,
            project_metadata=project_metadata
        )
        
        typer.echo(f"Successfully generated documentation for project {project_id}")
        return Response(html_content, mimetype='text/html')
            
    except requests.exceptions.RequestException as e:
        return redirect(url_for('home', error=f"Network error: {str(e)}"))
    except Exception as e:
        typer.echo(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('home', error=f"Unexpected error: {str(e)}"))
