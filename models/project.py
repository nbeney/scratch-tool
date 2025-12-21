"""Pydantic models for Scratch project.json files.

Based on the Scratch File Format specification:
https://en.scratch-wiki.info/wiki/Scratch_File_Format
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class Monitor(BaseModel):
    """A monitor (variable or list display) on the stage."""
    id: str
    mode: str  # "default", "large", "slider", "list"
    opcode: str  # e.g., "data_variable", "data_listcontents"
    params: Dict[str, Any]
    spriteName: Optional[str] = None
    value: Union[str, int, float, List[Any]]
    width: Optional[int] = None
    height: Optional[int] = None
    x: int
    y: int
    visible: bool
    sliderMin: Optional[int] = None
    sliderMax: Optional[int] = None
    isDiscrete: Optional[bool] = None


class Costume(BaseModel):
    """A costume (sprite image) or backdrop (stage image)."""
    name: str
    bitmapResolution: Optional[int] = None  # 1 for SVG, 2 for PNG
    dataFormat: str  # "svg", "png", "jpg"
    assetId: str
    md5ext: str
    rotationCenterX: Union[int, float]
    rotationCenterY: Union[int, float]


class Sound(BaseModel):
    """A sound asset."""
    name: str
    assetId: str
    dataFormat: str  # "wav", "mp3"
    format: str = ""  # Empty string or format info
    rate: int  # Sample rate (e.g., 48000)
    sampleCount: int
    md5ext: str


class Block(BaseModel):
    """A Scratch code block.
    
    Inputs format: Dict[name, array] where array is:
      [1, ...] - shadow block
      [2, ...] - no shadow
      [3, ..., ...] - obscured shadow (2nd element is input, 3rd is shadow)
    
    Fields format: Dict[name, array] where array is:
      [value] - simple field
      [value, id] - field with ID (for variables, broadcasts, etc.)
    """
    opcode: str
    next: Optional[str] = None  # ID of next block in sequence
    parent: Optional[str] = None  # ID of parent block
    inputs: Dict[str, Any] = Field(default_factory=dict)
    fields: Dict[str, List[Any]] = Field(default_factory=dict)
    shadow: bool
    topLevel: bool
    x: Optional[Union[int, float]] = None  # Only for top-level blocks
    y: Optional[Union[int, float]] = None  # Only for top-level blocks
    mutation: Optional[Dict[str, Any]] = None  # For custom blocks


class Comment(BaseModel):
    """A comment attached to a block or floating."""
    blockId: Optional[str] = None  # null if floating comment
    x: Union[int, float]
    y: Union[int, float]
    width: Union[int, float]
    height: Union[int, float]
    minimized: bool
    text: str


class Target(BaseModel):
    """A sprite or the stage."""
    isStage: bool
    name: str
    
    # Variables: Dict[id, [name, value]] or Dict[id, [name, value, true]] for cloud variables
    # The third element (if present and true) indicates this is a cloud variable
    variables: Dict[str, List[Union[str, int, float, bool]]] = Field(default_factory=dict)
    
    # Lists: Dict[id, [name, list_contents]]
    lists: Dict[str, List[Union[str, List[Any]]]] = Field(default_factory=dict)
    
    # Broadcasts: Dict[id, message_name]
    broadcasts: Dict[str, str] = Field(default_factory=dict)
    
    # Blocks: Dict[block_id, Block]
    blocks: Dict[str, Block] = Field(default_factory=dict)
    
    # Comments: Dict[comment_id, Comment]
    comments: Dict[str, Comment] = Field(default_factory=dict)
    
    currentCostume: int
    costumes: List[Costume]
    sounds: List[Sound]
    volume: Union[int, float]
    layerOrder: int
    
    # Stage-specific properties
    tempo: Optional[Union[int, float]] = None
    videoTransparency: Optional[Union[int, float]] = None
    videoState: Optional[str] = None  # "on", "off", "on-flipped"
    textToSpeechLanguage: Optional[str] = None
    
    # Sprite-specific properties
    visible: Optional[bool] = None
    x: Optional[Union[int, float]] = None
    y: Optional[Union[int, float]] = None
    size: Optional[Union[int, float]] = None
    direction: Optional[Union[int, float]] = None
    draggable: Optional[bool] = None
    rotationStyle: Optional[str] = None  # "all around", "left-right", "don't rotate"


class Meta(BaseModel):
    """Project metadata.
    
    According to Scratch File Format specification:
    - semver: Always "3.0.0" for Scratch 3.0 projects
    - vm: Scratch VM version used to create/save the project
    - agent: User agent string of the browser/editor
    """
    semver: str  # Scratch version (e.g., "3.0.0")
    vm: str  # VM version
    agent: str  # User agent string


class ScratchProject(BaseModel):
    """Complete Scratch 3.0 project.json structure.
    
    Based on the Scratch File Format specification:
    https://en.scratch-wiki.info/wiki/Scratch_File_Format
    
    Extensions are stored as an array of extension IDs (strings):
    - "pen" - Pen Extension
    - "music" - Music Extension
    - "videoSensing" - Video Sensing Extension
    - "text2speech" - Text to Speech Extension
    - "translate" - Translate Extension
    - "wedo2" - LEGO Education WeDo 2.0
    - "microbit" - micro:bit Extension
    - "ev3" - LEGO MINDSTORMS EV3
    - "makeymakey" - Makey Makey
    - "boost" - LEGO BOOST
    - "gdxfor" - Go Direct Force & Acceleration
    """
    targets: List[Target]
    monitors: List[Monitor] = Field(default_factory=list)
    extensions: List[str] = Field(default_factory=list)  # Extension IDs
    meta: Meta
    
    @property
    def stage(self) -> Optional[Target]:
        """Get the stage target."""
        for target in self.targets:
            if target.isStage:
                return target
        return None
    
    @property
    def sprites(self) -> List[Target]:
        """Get all sprite targets."""
        return [target for target in self.targets if not target.isStage]
    
    def get_sprite(self, name: str) -> Optional[Target]:
        """Get a sprite by name."""
        for target in self.targets:
            if not target.isStage and target.name == name:
                return target
        return None
    
    def get_all_variables(self) -> Dict[str, List[Union[str, int, float, bool]]]:
        """Get all variables from all targets."""
        all_vars = {}
        for target in self.targets:
            all_vars.update(target.variables)
        return all_vars
    
    def get_all_lists(self) -> Dict[str, List[Union[str, List[Any]]]]:
        """Get all lists from all targets."""
        all_lists = {}
        for target in self.targets:
            all_lists.update(target.lists)
        return all_lists
    
    def count_blocks(self) -> int:
        """Count total number of blocks in the project."""
        return sum(len(target.blocks) for target in self.targets)
    
    def count_sprites(self) -> int:
        """Count number of sprites (excluding stage)."""
        return len(self.sprites)
    
    def get_used_extensions(self) -> List[str]:
        """Get list of extension IDs used in the project."""
        return self.extensions
