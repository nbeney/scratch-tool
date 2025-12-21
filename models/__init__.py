"""Pydantic models for Scratch API and project files."""

from models.metadata import (
    Author,
    ErrorResponse,
    History,
    Profile,
    ProfileImages,
    ProjectImages,
    ProjectMetadata,
    Remix,
    Stats,
)
from models.project import (
    Block,
    BlockInput,
    Comment,
    Costume,
    Extension,
    Meta,
    Monitor,
    ScratchProject,
    Sound,
    Target,
)

__all__ = [
    # Metadata models
    "Author",
    "ErrorResponse",
    "History",
    "Profile",
    "ProfileImages",
    "ProjectImages",
    "ProjectMetadata",
    "Remix",
    "Stats",
    # Project models
    "Block",
    "BlockInput",
    "Comment",
    "Costume",
    "Extension",
    "Meta",
    "Monitor",
    "ScratchProject",
    "Sound",
    "Target",
]
