#!/usr/bin/env python3
"""Example script demonstrating how to use the Scratch project models."""

import sys
from pathlib import Path

from models.project import ScratchProject


def analyze_project(project_path: str) -> None:
    """Analyze a Scratch project.json file."""
    file_path = Path(project_path)
    
    if not file_path.exists():
        print(f"Error: File not found: {project_path}")
        sys.exit(1)
    
    print(f"Loading project: {file_path.name}")
    print("=" * 60)
    
    # Parse the project file with Pydantic
    with open(file_path) as f:
        project = ScratchProject.model_validate_json(f.read())
    
    # Basic project info
    print(f"\n📊 Project Overview:")
    print(f"  Semver: {project.meta.semver}")
    print(f"  VM: {project.meta.vm}")
    print(f"  User Agent: {project.meta.agent or 'N/A'}")
    
    # Stage information
    stage = project.stage
    print(f"\n🎭 Stage:")
    print(f"  Name: {stage.name}")
    print(f"  Costumes: {len(stage.costumes)}")
    print(f"  Sounds: {len(stage.sounds)}")
    print(f"  Variables: {len(stage.variables)}")
    print(f"  Lists: {len(stage.lists)}")
    print(f"  Blocks: {len(stage.blocks)}")
    
    # Sprites
    sprites = project.sprites
    print(f"\n🎮 Sprites ({len(sprites)}):")
    for sprite in sprites:
        print(f"  • {sprite.name}")
        print(f"    - Position: ({sprite.x}, {sprite.y})")
        print(f"    - Size: {sprite.size}%")
        print(f"    - Direction: {sprite.direction}°")
        print(f"    - Visible: {sprite.visible}")
        print(f"    - Costumes: {len(sprite.costumes)}")
        print(f"    - Sounds: {len(sprite.sounds)}")
        print(f"    - Blocks: {len(sprite.blocks)}")
    
    # Statistics
    print(f"\n📈 Statistics:")
    print(f"  Total Sprites: {project.count_sprites()}")
    print(f"  Total Blocks: {project.count_blocks()}")
    print(f"  Total Variables: {len(project.get_all_variables())}")
    print(f"  Total Lists: {len(project.get_all_lists())}")
    
    # Extensions
    if project.extensions:
        print(f"\n🔌 Extensions:")
        for ext in project.extensions:
            print(f"  • {ext}")
    
    # Monitors
    if project.monitors:
        print(f"\n👁️  Monitors ({len(project.monitors)}):")
        for monitor in project.monitors:
            print(f"  • {monitor.params.get('VARIABLE', 'Unknown')} ({monitor.mode})")
    
    # Block types used
    block_types = set()
    for target in project.targets:
        for block in target.blocks.values():
            block_types.add(block.opcode)
    
    print(f"\n🧩 Block Types Used ({len(block_types)}):")
    # Show first 10 block types
    for block_type in sorted(block_types)[:10]:
        print(f"  • {block_type}")
    if len(block_types) > 10:
        print(f"  ... and {len(block_types) - 10} more")
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python example_usage.py <path-to-project.json>")
        print("\nExample:")
        print("  python example_usage.py sample-project.json")
        sys.exit(1)
    
    analyze_project(sys.argv[1])
