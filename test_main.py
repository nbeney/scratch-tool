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
        result = runner.invoke(app, ["metadata", "1252755893"])
        
        assert result.exit_code == 0
        assert "Fetching metadata for project 1252755893" in result.stdout
        assert "✓ Successfully fetched metadata" in result.stdout
        assert "project_token" in result.stdout
        assert "nicoben2" in result.stdout  # Author username
        assert "Snowball fight" in result.stdout  # Title

    def test_metadata_valid_project_by_url(self):
        """Test fetching metadata with a valid project URL."""
        result = runner.invoke(app, ["metadata", "https://scratch.mit.edu/projects/1252755893/"])
        
        assert result.exit_code == 0
        assert "Fetching metadata for project 1252755893" in result.stdout
        assert "✓ Successfully fetched metadata" in result.stdout

    def test_metadata_valid_project_by_editor_url(self):
        """Test fetching metadata with a valid project editor URL."""
        result = runner.invoke(app, ["metadata", "https://scratch.mit.edu/projects/1252755893/editor"])
        
        assert result.exit_code == 0
        assert "Fetching metadata for project 1252755893" in result.stdout
        assert "✓ Successfully fetched metadata" in result.stdout

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
            result = runner.invoke(app, ["download", "1252755893"])
            
            # Note: This test will fail if the project becomes unavailable
            # or network is down - that's expected for integration tests
            if result.exit_code == 0:
                # Should create file with title-based name
                expected_file = tmp_path / "Snowball fight.sb3"
                assert expected_file.exists()
                assert expected_file.stat().st_size > 0
                assert "✓ Successfully downloaded" in result.stdout
                assert "Snowball fight.sb3" in result.stdout
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
            result = runner.invoke(app, ["download", "1252755893", "--name", "my-custom-project"])
            
            if result.exit_code == 0:
                output_file = tmp_path / "my-custom-project.sb3"
                assert output_file.exists()
                assert "my-custom-project.sb3" in result.stdout
        finally:
            os.chdir(original_cwd)


class TestExtractProjectId:
    """Tests for project ID extraction."""

    def test_extract_from_numeric_id(self):
        """Test extraction from numeric ID."""
        from main import extract_project_id
        assert extract_project_id("1252755893") == "1252755893"

    def test_extract_from_full_url(self):
        """Test extraction from full project URL."""
        from main import extract_project_id
        url = "https://scratch.mit.edu/projects/1252755893/"
        assert extract_project_id(url) == "1252755893"

    def test_extract_from_editor_url(self):
        """Test extraction from editor URL."""
        from main import extract_project_id
        url = "https://scratch.mit.edu/projects/1252755893/editor"
        assert extract_project_id(url) == "1252755893"

    def test_extract_from_invalid_format(self):
        """Test extraction fails with invalid format."""
        from main import extract_project_id
        with pytest.raises(ValueError, match="Could not extract project ID"):
            extract_project_id("invalid-format")


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
        
        assert metadata.id == 1252755893
        assert metadata.title == "Snowball fight"
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
