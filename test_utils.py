"""Integration tests for scratch-tool commands."""

import pytest

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
