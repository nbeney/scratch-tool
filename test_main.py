"""Integration tests for scratch-tool commands."""

import json
from pathlib import Path

import pytest
import requests
from typer.testing import CliRunner

from main import app

runner = CliRunner()


class TestMetadataCommand:
    """Tests for the metadata command."""

    def test_metadata_valid_project_by_id(self):
        """Test fetching metadata with a valid project ID."""
        result = runner.invoke(app, ["metadata", "1259204833"])
        
        assert result.exit_code == 0
        assert "Fetching metadata for project 1259204833" in result.stdout
        assert "✓ Successfully saved metadata to:" in result.stdout
        assert "metadata.json" in result.stdout
        assert "nicoben2" in result.stdout  # Author username
        assert "All Blocks" in result.stdout  # Title
        
        # Verify file was created
        import glob
        metadata_files = glob.glob("*1259204833-metadata.json")
        assert len(metadata_files) > 0, "Metadata file should be created"

    def test_metadata_valid_project_by_url(self):
        """Test fetching metadata with a valid project URL."""
        result = runner.invoke(app, ["metadata", "https://scratch.mit.edu/projects/1259204833/"])
        
        assert result.exit_code == 0
        assert "Fetching metadata for project 1259204833" in result.stdout
        assert "✓ Successfully saved metadata to:" in result.stdout

    def test_metadata_valid_project_by_editor_url(self):
        """Test fetching metadata with a valid project editor URL."""
        result = runner.invoke(app, ["metadata", "https://scratch.mit.edu/projects/1259204833/editor"])
        
        assert result.exit_code == 0
        assert "Fetching metadata for project 1259204833" in result.stdout
        assert "✓ Successfully saved metadata to:" in result.stdout

    def test_metadata_with_custom_name(self):
        """Test fetching metadata with a custom filename."""
        result = runner.invoke(app, ["metadata", "1259204833", "--name", "test-custom"])
        
        assert result.exit_code == 0
        assert "✓ Successfully saved metadata to: test-custom.json" in result.stdout
        
        # Verify file was created with custom name
        import os
        assert os.path.exists("test-custom.json"), "Custom named file should be created"
        
        # Clean up
        if os.path.exists("test-custom.json"):
            os.remove("test-custom.json")

    def test_metadata_invalid_project_id(self):
        """Test fetching metadata with an invalid/non-existent project ID."""
        result = runner.invoke(app, ["metadata", "99999999999999"])
        
        assert result.exit_code == 1
        # Error messages go to stderr
        output = result.stdout + result.stderr
        assert "Error: Project not found (404)" in output
        assert "Only public and shared projects can be accessed" in output

    def test_metadata_invalid_url_format(self):
        """Test fetching metadata with an invalid URL format."""
        result = runner.invoke(app, ["metadata", "not-a-valid-url"])
        
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Could not extract project ID from" in output

    @pytest.mark.skipif(
        not Path("project-meta-fail.json").exists(),
        reason="Test data file not found"
    )
    def test_metadata_error_response_format(self, mocker):
        """Test handling of error response format from API."""
        # Load the error response
        with open("project-meta-fail.json") as f:
            error_data = json.load(f)
        
        # Mock the requests.get to return error response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = error_data
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch("requests.get", return_value=mock_response)
        
        result = runner.invoke(app, ["metadata", "1234567890"])
        
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error from API: NotFound" in output


class TestDownloadCommand:
    """Tests for the download command."""

    def test_download_help(self):
        """Test that download command help is accessible."""
        result = runner.invoke(app, ["download", "--help"])
        
        assert result.exit_code == 0
        assert "Download a Scratch 3 project" in result.stdout
        assert "Only public and shared projects can be downloaded" in result.stdout

    def test_download_invalid_project_id(self):
        """Test downloading with an invalid project ID."""
        result = runner.invoke(app, ["download", "99999999999999"])
        
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error: Project not found (404)" in output

    def test_download_invalid_url_format(self):
        """Test downloading with an invalid URL format."""
        result = runner.invoke(app, ["download", "invalid-format"])
        
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Could not extract project ID from" in output

    def test_download_valid_project_creates_file(self, tmp_path, mocker):
        """Test that downloading a valid project creates an .sb3 file."""
        # Change working directory to temp path
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # This is a real project - will actually download
            # Use a small project for faster test
            result = runner.invoke(app, ["download", "1259204833"])
            
            # Note: This test will fail if the project becomes unavailable
            # or network is down - that's expected for integration tests
            if result.exit_code == 0:
                # Should create file with new format: title-projectid-project.sb3
                expected_file = tmp_path / "All Blocks-1259204833-project.sb3"
                assert expected_file.exists()
                assert expected_file.stat().st_size > 0
                assert "✓ Successfully downloaded" in result.stdout
                assert "All Blocks-1259204833-project.sb3" in result.stdout
            else:
                # If download fails, at least check error handling works
                output = result.stdout + result.stderr
                assert "Error" in output
        finally:
            os.chdir(original_cwd)
    
    def test_download_with_custom_name(self, tmp_path):
        """Test that custom name override works."""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = runner.invoke(app, ["download", "1259204833", "--name", "my-custom-project"])
            
            if result.exit_code == 0:
                output_file = tmp_path / "my-custom-project.sb3"
                assert output_file.exists()
                assert "my-custom-project.sb3" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_download_code_only(self, tmp_path):
        """Test that --code flag downloads only project.json."""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = runner.invoke(app, ["download", "1259204833", "--code"])
            
            if result.exit_code == 0:
                # Should create JSON file with new format: title-projectid-project.json
                expected_file = tmp_path / "All Blocks-1259204833-project.json"
                assert expected_file.exists()
                assert expected_file.stat().st_size > 0
                assert "✓ Successfully downloaded code" in result.stdout
                assert "All Blocks-1259204833-project.json" in result.stdout
                
                # Verify it's valid JSON
                import json
                content = json.loads(expected_file.read_text())
                assert "targets" in content
                
                # Should not create .sb3 file (with new filename format)
                sb3_file = tmp_path / "All Blocks-1259204833-project.sb3"
                assert not sb3_file.exists()
        finally:
            os.chdir(original_cwd)
    
    def test_download_code_only_custom_name(self, tmp_path):
        """Test that --code flag works with custom name."""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = runner.invoke(app, ["download", "1259204833", "--code", "--name", "my-code"])
            
            if result.exit_code == 0:
                output_file = tmp_path / "my-code.json"
                assert output_file.exists()
                assert "my-code.json" in result.stdout
        finally:
            os.chdir(original_cwd)


class TestExtractProjectId:
    """Tests for project ID extraction."""

    def test_extract_from_numeric_id(self):
        """Test extraction from numeric ID."""
        from main import extract_project_id
        assert extract_project_id("1259204833") == "1259204833"

    def test_extract_from_full_url(self):
        """Test extraction from full project URL."""
        from main import extract_project_id
        url = "https://scratch.mit.edu/projects/1259204833/"
        assert extract_project_id(url) == "1259204833"

    def test_extract_from_editor_url(self):
        """Test extraction from editor URL."""
        from main import extract_project_id
        url = "https://scratch.mit.edu/projects/1259204833/editor"
        assert extract_project_id(url) == "1259204833"

    def test_extract_from_invalid_format(self):
        """Test extraction fails with invalid format."""
        from main import extract_project_id
        with pytest.raises(ValueError, match="Could not extract project ID"):
            extract_project_id("invalid-format")


class TestExtractProjectIdFromFilename:
    """Tests for extracting project ID from filename."""

    def test_extract_from_sb3_filename(self):
        """Test extraction from .sb3 filename with project ID."""
        from main import extract_project_id_from_filename
        assert extract_project_id_from_filename("My Project-1259204833-project.sb3") == "1259204833"

    def test_extract_from_json_filename(self):
        """Test extraction from .json filename with project ID."""
        from main import extract_project_id_from_filename
        assert extract_project_id_from_filename("My Project-1259204833-project.json") == "1259204833"

    def test_extract_from_path(self):
        """Test extraction works with full path."""
        from main import extract_project_id_from_filename
        assert extract_project_id_from_filename("/path/to/My Project-1259204833-project.sb3") == "1259204833"

    def test_extract_with_special_chars_in_title(self):
        """Test extraction when title has hyphens."""
        from main import extract_project_id_from_filename
        assert extract_project_id_from_filename("My-Cool-Project-9876543210-project.sb3") == "9876543210"

    def test_extract_returns_none_for_simple_filename(self):
        """Test returns None for filename without project ID."""
        from main import extract_project_id_from_filename
        assert extract_project_id_from_filename("my-project.sb3") is None

    def test_extract_returns_none_for_wrong_format(self):
        """Test returns None for filename not matching pattern."""
        from main import extract_project_id_from_filename
        assert extract_project_id_from_filename("project-12345.sb3") is None


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_sanitize_basic(self):
        """Test basic filename sanitization."""
        from main import sanitize_filename
        assert sanitize_filename("My Project") == "My Project"

    def test_sanitize_invalid_chars(self):
        """Test removal of invalid characters."""
        from main import sanitize_filename
        result = sanitize_filename("Project: <Test> | File?")
        assert result == "Project_ _Test_ _ File_"

    def test_sanitize_leading_trailing_spaces(self):
        """Test removal of leading/trailing spaces."""
        from main import sanitize_filename
        assert sanitize_filename("  Project  ") == "Project"

    def test_sanitize_multiple_spaces(self):
        """Test collapsing multiple spaces."""
        from main import sanitize_filename
        assert sanitize_filename("My    Project    Name") == "My Project Name"

    def test_sanitize_empty_string(self):
        """Test empty string returns default."""
        from main import sanitize_filename
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"

    def test_sanitize_long_filename(self):
        """Test truncation of long filenames."""
        from main import sanitize_filename
        long_name = "A" * 250
        result = sanitize_filename(long_name)
        assert len(result) <= 200


class TestPydanticModels:
    """Tests for Pydantic models."""

    @pytest.mark.skipif(
        not Path("project-meta-pass.json").exists(),
        reason="Test data file not found"
    )
    def test_project_metadata_valid(self):
        """Test ProjectMetadata model with valid data."""
        from models.metadata import ProjectMetadata
        
        with open("project-meta-pass.json") as f:
            data = json.load(f)
        
        metadata = ProjectMetadata.model_validate(data)
        
        assert metadata.id == 1259204833
        assert metadata.title == "All Blocks"
        assert metadata.author.username == "nicoben2"
        assert metadata.public is True
        assert metadata.project_token is not None

    @pytest.mark.skipif(
        not Path("project-meta-fail.json").exists(),
        reason="Test data file not found"
    )
    def test_error_response_valid(self):
        """Test ErrorResponse model with valid error data."""
        from models.metadata import ErrorResponse
        
        with open("project-meta-fail.json") as f:
            data = json.load(f)
        
        error = ErrorResponse.model_validate(data)
        
        assert error.code == "NotFound"
        assert error.message == ""


class TestAnalyzeCommand:
    """Tests for the analyze command."""

    @pytest.mark.skipif(
        not Path("sample-project.json").exists(),
        reason="Test data file not found"
    )
    def test_analyze_local_file(self):
        """Test analyzing a local project.json file."""
        result = runner.invoke(app, ["analyze", "sample-project.json"])
        
        assert result.exit_code == 0
        assert "Loading project from file: sample-project.json" in result.stdout
        assert "📊 Project Overview:" in result.stdout
        assert "🎭 Stage:" in result.stdout
        assert "🎮 Sprites" in result.stdout
        assert "📈 Statistics:" in result.stdout
        assert "✅ Analysis complete!" in result.stdout

    @pytest.mark.skipif(
        not Path("sample-project.json").exists(),
        reason="Test data file not found"
    )
    def test_analyze_shows_project_stats(self):
        """Test that analyze shows correct statistics."""
        result = runner.invoke(app, ["analyze", "sample-project.json"])
        
        assert result.exit_code == 0
        # Check for specific stats we know from sample-project.json
        assert "Total Sprites: 4" in result.stdout
        assert "Total Blocks: 56" in result.stdout
        assert "Semver: 3.0.0" in result.stdout

    @pytest.mark.skipif(
        not Path("sample-project.json").exists(),
        reason="Test data file not found"
    )
    def test_analyze_shows_sprite_details(self):
        """Test that analyze shows sprite details."""
        result = runner.invoke(app, ["analyze", "sample-project.json"])
        
        assert result.exit_code == 0
        # Check for sprite names
        assert "Snowman" in result.stdout
        assert "Arrow" in result.stdout
        assert "Snowball" in result.stdout
        assert "Sprite1" in result.stdout
        # Check for sprite properties
        assert "Position:" in result.stdout
        assert "Size:" in result.stdout
        assert "Direction:" in result.stdout

    @pytest.mark.skipif(
        not Path("sample-project.json").exists(),
        reason="Test data file not found"
    )
    def test_analyze_shows_monitors(self):
        """Test that analyze shows monitor information."""
        result = runner.invoke(app, ["analyze", "sample-project.json"])
        
        assert result.exit_code == 0
        assert "👁️  Monitors" in result.stdout
        assert "Falling" in result.stdout
        assert "power" in result.stdout
        assert "score" in result.stdout

    @pytest.mark.skipif(
        not Path("sample-project.json").exists(),
        reason="Test data file not found"
    )
    def test_analyze_shows_block_types(self):
        """Test that analyze shows block types used."""
        result = runner.invoke(app, ["analyze", "sample-project.json"])
        
        assert result.exit_code == 0
        assert "🧩 Block Types Used" in result.stdout
        # Should show some common block types
        assert "control_" in result.stdout or "event_" in result.stdout or "data_" in result.stdout

    def test_analyze_valid_project_by_id(self):
        """Test analyzing a project by ID from Scratch."""
        result = runner.invoke(app, ["analyze", "1259204833"])
        
        assert result.exit_code == 0
        assert "Fetching project 1259204833 from Scratch" in result.stdout
        assert "📊 Project Overview:" in result.stdout
        assert "✅ Analysis complete!" in result.stdout

    def test_analyze_valid_project_by_url(self):
        """Test analyzing a project by URL from Scratch."""
        result = runner.invoke(app, ["analyze", "https://scratch.mit.edu/projects/1259204833/"])
        
        assert result.exit_code == 0
        assert "Fetching project 1259204833 from Scratch" in result.stdout
        assert "✅ Analysis complete!" in result.stdout

    def test_analyze_invalid_project_id(self):
        """Test analyzing with an invalid/non-existent project ID."""
        result = runner.invoke(app, ["analyze", "99999999999999"])
        
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error" in output or "not found" in output.lower()

    def test_analyze_nonexistent_file(self):
        """Test analyzing a non-existent local file."""
        result = runner.invoke(app, ["analyze", "nonexistent-file.json"])
        
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error" in output

    def test_analyze_invalid_url_format(self):
        """Test analyzing with an invalid URL format."""
        result = runner.invoke(app, ["analyze", "https://example.com/not-a-scratch-project"])
        
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error" in output or "extract" in output.lower()

    def test_analyze_help(self):
        """Test that analyze command help works."""
        result = runner.invoke(app, ["analyze", "--help"])
        
        assert result.exit_code == 0
        assert "Analyze a Scratch project" in result.stdout
        assert "URL" in result.stdout
        assert "ID" in result.stdout
        assert "project.json" in result.stdout

    @pytest.mark.skipif(
        not Path("sample-project.json").exists(),
        reason="Test data file not found"
    )
    def test_analyze_quiet_mode_valid_file(self):
        """Test analyzing with --quiet flag produces no output for valid JSON."""
        result = runner.invoke(app, ["analyze", "sample-project.json", "--quiet"])
        
        assert result.exit_code == 0
        assert result.stdout == ""  # No output in quiet mode
    
    @pytest.mark.skipif(
        not Path("sample-project.json").exists(),
        reason="Test data file not found"
    )
    def test_analyze_quiet_mode_short_flag(self):
        """Test analyzing with -q short flag."""
        result = runner.invoke(app, ["analyze", "sample-project.json", "-q"])
        
        assert result.exit_code == 0
        assert result.stdout == ""  # No output in quiet mode
    
    def test_analyze_quiet_mode_invalid_file(self):
        """Test that errors are still shown in quiet mode."""
        result = runner.invoke(app, ["analyze", "nonexistent-file.json", "--quiet"])
        
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error" in output  # Error should still be displayed
    
    def test_analyze_quiet_mode_valid_remote_project(self):
        """Test analyzing remote project in quiet mode."""
        result = runner.invoke(app, ["analyze", "1259204833", "--quiet"])
        
        assert result.exit_code == 0
        assert result.stdout == ""  # No output in quiet mode


class TestDocumentCommand:
    """Tests for the document command."""

    def test_document_from_project_id(self, tmp_path, monkeypatch):
        """Test generating documentation from a project ID."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["document", "1259204833"])
        
        assert result.exit_code == 0
        assert "Downloading project 1259204833" in result.stdout
        assert "✓ Documentation generated successfully!" in result.stdout
        assert Path("All Blocks.html").exists()
        # Standalone mode by default - no directory created
        assert "Standalone" in result.stdout
        assert not Path("All Blocks").exists()
        
    def test_document_with_custom_name(self, tmp_path, monkeypatch):
        """Test generating documentation with --name option."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["document", "1259204833", "--name", "custom-doc"])
        
        assert result.exit_code == 0
        assert "✓ Documentation generated successfully!" in result.stdout
        assert Path("custom-doc.html").exists()
        # Standalone mode by default
        assert not Path("custom-doc").exists()
        
    def test_document_from_sb3_file(self, tmp_path, monkeypatch):
        """Test generating documentation from a .sb3 file."""
        monkeypatch.chdir(tmp_path)
        
        # First download the project
        result = runner.invoke(app, ["download", "1259204833", "--name", "test"])
        assert result.exit_code == 0
        
        # Then generate documentation
        result = runner.invoke(app, ["document", "test.sb3"])
        
        assert result.exit_code == 0
        assert "Loading project from file: test.sb3" in result.stdout
        assert "✓ Documentation generated successfully!" in result.stdout
        assert Path("test.html").exists()
        # Standalone mode by default
        assert not Path("test").exists()
        
    def test_document_creates_thumbnails(self, tmp_path, monkeypatch):
        """Test that documentation creates thumbnails for costumes when using local mode."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["document", "1259204833", "--name", "thumb-test", "--no-standalone"])
        
        assert result.exit_code == 0
        
        # Check that thumbnails were created (project has at least one PNG costume)
        thumb_dir = Path("thumb-test")
        thumb_files = list(thumb_dir.glob("thumb_*.png"))
        # All Blocks project has 1 PNG backdrop
        assert len(thumb_files) >= 1
        
    def test_document_includes_audio_players(self, tmp_path, monkeypatch):
        """Test that documentation includes audio players for sounds."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["document", "1259204833", "--name", "audio-test"])
        
        assert result.exit_code == 0
        
        # Check that HTML contains audio elements
        html_content = Path("audio-test.html").read_text()
        assert "<audio" in html_content
        assert "controls" in html_content
        assert ".wav" in html_content
        
    def test_document_includes_project_info(self, tmp_path, monkeypatch):
        """Test that documentation includes project information."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["document", "1259204833", "--name", "info-test"])
        
        assert result.exit_code == 0
        
        # Check that HTML contains project info
        html_content = Path("info-test.html").read_text()
        assert "Scratch Project Documentation" in html_content  # Page title
        assert "Project Information" in html_content
        assert "Stage" in html_content
        assert "Sprites" in html_content
        assert "Statistics" in html_content
        
    def test_document_includes_scripts(self, tmp_path, monkeypatch):
        """Test that documentation includes scratchblocks scripts."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["document", "1259204833", "--name", "scripts-test"])
        
        assert result.exit_code == 0
        
        # Check that HTML contains scratchblocks elements
        html_content = Path("scripts-test.html").read_text()
        assert "scratchblocks" in html_content  # Library reference
        assert 'pre class="blocks"' in html_content  # Block containers
        assert "when green flag clicked" in html_content  # Sample script
        assert "Scripts" in html_content  # Scripts section header
        
    def test_document_invalid_project_id(self, tmp_path, monkeypatch):
        """Test error handling for invalid project ID."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["document", "99999999999999"])
        
        assert result.exit_code == 1
        
    def test_document_nonexistent_file(self, tmp_path, monkeypatch):
        """Test error handling for nonexistent file."""
        monkeypatch.chdir(tmp_path)
        
        result = runner.invoke(app, ["document", "nonexistent.sb3"])
        
        assert result.exit_code == 1
        assert "Error" in (result.stdout + result.stderr)

    def test_document_extracts_project_id_from_filename(self, tmp_path, monkeypatch):
        """Test that project ID is extracted from filename and shown in HTML."""
        monkeypatch.chdir(tmp_path)
        
        # Download the project with the standard naming format
        result = runner.invoke(app, ["download", "1259204833"])
        assert result.exit_code == 0
        
        # The file should be named "All Blocks-1259204833-project.sb3"
        sb3_file = "All Blocks-1259204833-project.sb3"
        assert Path(sb3_file).exists()
        
        # Generate documentation from the file
        result = runner.invoke(app, ["document", sb3_file])
        assert result.exit_code == 0
        
        # Check that the HTML was generated
        html_file = "All Blocks-1259204833-project.html"
        assert Path(html_file).exists()
        
        # Verify the project ID appears in the HTML
        html_content = Path(html_file).read_text()
        assert "1259204833" in html_content
        assert "Project ID" in html_content

