"""Tests for Scratch project.json Pydantic models."""

import json
from pathlib import Path

import pytest

from models.project import ScratchProject


class TestScratchProjectModel:
    """Tests for the ScratchProject Pydantic model."""

    def test_parse_sample_project(self):
        """Test parsing a real Scratch project.json file."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        # Parse with Pydantic model
        project = ScratchProject.model_validate(project_data)
        
        # Basic assertions
        assert project is not None
        assert len(project.targets) > 0
        assert project.meta is not None
        
    def test_stage_property(self):
        """Test the stage property."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        stage = project.stage
        assert stage is not None
        assert stage.isStage is True
        assert stage.name == "Stage"
    
    def test_sprites_property(self):
        """Test the sprites property."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        sprites = project.sprites
        assert isinstance(sprites, list)
        assert all(not sprite.isStage for sprite in sprites)
    
    def test_count_blocks(self):
        """Test counting blocks in the project."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        block_count = project.count_blocks()
        assert block_count >= 0
        assert isinstance(block_count, int)
    
    def test_count_sprites(self):
        """Test counting sprites."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        sprite_count = project.count_sprites()
        assert sprite_count >= 0
        assert isinstance(sprite_count, int)
    
    def test_get_sprite_by_name(self):
        """Test getting a sprite by name."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        # Try to get first sprite
        if project.sprites:
            first_sprite_name = project.sprites[0].name
            found_sprite = project.get_sprite(first_sprite_name)
            assert found_sprite is not None
            assert found_sprite.name == first_sprite_name
        
        # Try non-existent sprite
        assert project.get_sprite("NonExistentSprite") is None
    
    def test_target_has_costumes(self):
        """Test that targets have costumes."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        for target in project.targets:
            assert hasattr(target, 'costumes')
            assert isinstance(target.costumes, list)
            if target.costumes:
                costume = target.costumes[0]
                assert costume.name is not None
                assert costume.assetId is not None
                assert costume.md5ext is not None
    
    def test_target_has_sounds(self):
        """Test that targets have sounds."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        for target in project.targets:
            assert hasattr(target, 'sounds')
            assert isinstance(target.sounds, list)
    
    def test_get_all_variables(self):
        """Test getting all variables."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        all_vars = project.get_all_variables()
        assert isinstance(all_vars, dict)
    
    def test_get_all_lists(self):
        """Test getting all lists."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        all_lists = project.get_all_lists()
        assert isinstance(all_lists, dict)
    
    def test_blocks_structure(self):
        """Test that blocks have proper structure."""
        project_file = Path("sample-project.json")
        
        if not project_file.exists():
            pytest.skip("sample-project.json not found")
        
        with open(project_file) as f:
            project_data = json.load(f)
        
        project = ScratchProject.model_validate(project_data)
        
        for target in project.targets:
            for block_id, block in target.blocks.items():
                assert block.opcode is not None
                assert isinstance(block.shadow, bool)
                assert isinstance(block.topLevel, bool)
                assert isinstance(block.inputs, dict)
                assert isinstance(block.fields, dict)
