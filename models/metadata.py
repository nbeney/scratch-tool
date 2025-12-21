"""Pydantic models for Scratch API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProfileImages(BaseModel):
    """Profile image URLs."""
    image_90x90: str = Field(alias="90x90")
    image_60x60: str = Field(alias="60x60")
    image_55x55: str = Field(alias="55x55")
    image_50x50: str = Field(alias="50x50")
    image_32x32: str = Field(alias="32x32")


class Profile(BaseModel):
    """User profile information."""
    id: Optional[int] = None
    images: ProfileImages


class History(BaseModel):
    """User or project history."""
    joined: Optional[datetime] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    shared: Optional[datetime] = None


class Author(BaseModel):
    """Project author information."""
    id: int
    username: str
    scratchteam: bool
    history: History
    profile: Profile


class ProjectImages(BaseModel):
    """Project thumbnail URLs."""
    image_282x218: str = Field(alias="282x218")
    image_216x163: str = Field(alias="216x163")
    image_200x200: str = Field(alias="200x200")
    image_144x108: str = Field(alias="144x108")
    image_135x102: str = Field(alias="135x102")
    image_100x80: str = Field(alias="100x80")


class Stats(BaseModel):
    """Project statistics."""
    views: int
    loves: int
    favorites: int
    remixes: int


class Remix(BaseModel):
    """Project remix information."""
    parent: Optional[int] = None
    root: Optional[int] = None


class ProjectMetadata(BaseModel):
    """Complete project metadata from Scratch API."""
    id: int
    title: str
    description: str
    instructions: str
    visibility: str
    public: bool
    comments_allowed: bool
    is_published: bool
    author: Author
    image: str
    images: ProjectImages
    history: History
    stats: Stats
    remix: Remix
    project_token: str


class ErrorResponse(BaseModel):
    """Error response from Scratch API."""
    code: str
    message: str
