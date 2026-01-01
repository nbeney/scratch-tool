import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests
import typer
from flask import Flask, request, render_template_string, send_file, redirect, url_for
from dominate import document as dom_document
from dominate.tags import (
    a, audio, body, div, h1, h2, h3, head, html, img, li, link, meta, pre, script, source, style, title, ul
)
from dominate.util import raw, text
from PIL import Image
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer
from pydantic import ValidationError

from models.metadata import ErrorResponse, ProjectMetadata
from models.project import ScratchProject
from scratchblocks_converter import target_to_scratchblocks

from utils import extract_project_id, extract_project_id_from_filename, sanitize_filename, print_colored_json


def generate_html_documentation(
    project: ScratchProject,
    project_json: dict,
    costume_thumbnails: dict,
    sound_files: dict,
    output_name: str,
    standalone: bool = True,
    project_id: Optional[str] = None,
    project_metadata: Optional[ProjectMetadata] = None
) -> str:
    """Generate HTML documentation for a Scratch project using dominate.
    
    Args:
        project: Parsed Scratch project
        project_json: Raw project JSON
        costume_thumbnails: Dict mapping md5ext to thumbnail path/URL
        sound_files: Dict mapping md5ext to sound file path/URL
        output_name: Base name for output files
        standalone: If True, URLs are CDN links; if False, local paths
        project_id: Optional Scratch project ID
        project_metadata: Optional project metadata from Scratch API (includes title, author, remix info)
    """
    
    # Determine the title to display
    page_title = project_metadata.title if project_metadata else output_name
    
    doc = dom_document(title=f'{page_title} - Scratch Project Documentation')
    
    with doc.head:
        meta(charset='UTF-8')
        meta(name='viewport', content='width=device-width, initial-scale=1.0')
        
        # Scratchblocks CSS
        link(rel='stylesheet', href='https://cdn.jsdelivr.net/npm/scratchblocks@3.6.4/build/scratchblocks.min.css')
        
        # CSS styles
        style("""
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            display: flex;
        }
        .sidebar {
            width: 280px;
            background: white;
            padding: 20px;
            border-right: 2px solid #e0e0e0;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            flex-shrink: 0;
        }
        .sidebar-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #ff6680;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ff6680;
        }
        .sidebar-nav {
            list-style: none;
        }
        .sidebar-nav > li {
            margin-bottom: 5px;
        }
        .sidebar-nav a {
            display: block;
            padding: 10px 15px;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .sidebar-nav a:hover {
            background: #f0f0f0;
            color: #ff6680;
            transform: translateX(5px);
        }
        .sidebar-nav a.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }
        .sidebar-nav .sprite-subnav {
            list-style: none;
            margin-top: 5px;
            margin-left: 15px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        .sidebar-nav .sprite-subnav.expanded {
            max-height: 2000px;
        }
        .sidebar-nav .sprite-subnav li {
            margin-bottom: 3px;
        }
        .sidebar-nav .sprite-subnav a {
            padding: 8px 12px;
            font-size: 0.9em;
            font-weight: 400;
            color: #666;
        }
        .sidebar-nav .sprite-subnav a:hover {
            color: #4a90e2;
            background: #e8f4fd;
        }
        .sidebar-nav .sprite-subnav a.active {
            background: #4a90e2;
            color: white;
        }
        .main-content {
            flex: 1;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        h1, h2, h3 {
            color: #ff6680;
        }
        .section {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 15px;
        }
        .metadata-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .metadata-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }
        .sprite {
            border: 2px solid #ddd;
            padding: 15px;
            margin: 15px 0;
            border-radius: 8px;
            background: #fafafa;
        }
        .sprite-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        .sprite-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #4a90e2;
        }
        .sprite-props {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(75px, 1fr));
            gap: 8px;
            margin: 10px 0;
        }
        .prop {
            background: white;
            padding: 6px;
            border-radius: 4px;
            border-left: 3px solid #4a90e2;
        }
        .prop-label {
            font-size: 0.75em;
            color: #666;
        }
        .prop-value {
            font-weight: bold;
            color: #333;
            font-size: 0.9em;
        }
        .assets {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 15px 0;
        }
        .asset {
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .asset img {
            max-width: 150px;
            max-height: 150px;
            display: block;
            margin: 0 auto 10px;
            border: 1px solid #eee;
        }
        .asset-name {
            font-size: 0.9em;
            color: #333;
            word-break: break-word;
        }
        .audio-player {
            margin-top: 10px;
        }
        .variables-section {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        .variable {
            background: white;
            padding: 12px;
            border-radius: 4px;
            border: 1px solid #ddd;
            border-left: 4px solid #ff8c1a;
        }
        .variable-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        .variable-value {
            color: #666;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.85em;
            word-break: break-word;
        }
        .lists-section {
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin: 15px 0;
        }
        .list {
            background: white;
            padding: 12px;
            border-radius: 4px;
            border: 1px solid #ddd;
            border-left: 4px solid #cc5b22;
        }
        .list-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            font-size: 0.9em;
        }
        .list-values {
            background: #f9f9f9;
            padding: 10px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.85em;
        }
        .list-item {
            padding: 3px 0;
            color: #555;
        }
        .list-more {
            padding: 5px 0;
            color: #888;
            font-style: italic;
        }
        .messages-section {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        .message {
            background: white;
            padding: 12px;
            border-radius: 4px;
            border: 1px solid #ddd;
            border-left: 4px solid #ffab19;
        }
        .message-name {
            font-weight: 600;
            color: #333;
            font-size: 0.9em;
        }
        .blocks-count {
            background: #e8f4fd;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            border-left: 4px solid #4a90e2;
        }
        .extensions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .extension {
            background: #fef3cd;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            border: 1px solid #f5c842;
        }
        .statistics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            margin: 8px 0;
        }
        .stat-label {
            font-size: 0.85em;
            opacity: 0.9;
        }
        .scripts-section {
            margin-top: 20px;
        }
        .script {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 4px solid #ff6680;
        }
        pre.blocks {
            margin: 0;
            padding: 10px;
            background: white;
            border-radius: 4px;
            overflow-x: auto;
        }
        """)
    
    with doc:
        # Sidebar
        with div(cls='sidebar'):
            div('🎨 Navigation', cls='sidebar-title')
            with ul(cls='sidebar-nav'):
                with li():
                    a('📋 Info', href='#info')
                with li():
                    a('📊 Statistics', href='#statistics')
                if project.extensions:
                    with li():
                        a('🔌 Extensions', href='#extensions')
                with li():
                    a('🎭 Stage', href='#stage')
                with li():
                    a('🎮 Sprites', href='#sprites', cls='sprites-toggle')
                    # Sprite subnav - will be populated with sprite links
                    with ul(cls='sprite-subnav expanded', id='sprite-subnav'):
                        for sprite in project.sprites:
                            # Create valid ID from sprite name
                            sprite_id = f"sprite-{sprite.name.lower().replace(' ', '-')}"
                            with li():
                                a(sprite.name, href=f'#{sprite_id}')
        
        # Main content area
        with div(cls='main-content'):
            h1(f'🎨 {page_title}')
            
            # Project Information Section
            with div(cls='section', id='info'):
                h2('Project Information')
                with div(cls='metadata'):
                    if project_metadata:
                        with div(cls='metadata-item'):
                            div('Author', cls='metadata-label')
                            with div():
                                a(project_metadata.author.username, 
                                  href=f'https://scratch.mit.edu/users/{project_metadata.author.username}/',
                                  target='_blank')
                        with div(cls='metadata-item'):
                            div('Remix', cls='metadata-label')
                            if project_metadata.remix.parent:
                                with div():
                                    raw('Yes (parent: ')
                                    a(str(project_metadata.remix.parent), 
                                      href=f'https://scratch.mit.edu/projects/{project_metadata.remix.parent}/',
                                      target='_blank')
                                    raw(')')
                            else:
                                div('No')
                    with div(cls='metadata-item'):
                        div('Project ID', cls='metadata-label')
                        if project_id:
                            with div():
                                a(project_id, 
                                  href=f'https://scratch.mit.edu/projects/{project_id}/',
                                  target='_blank')
                        else:
                            div('-')
                    with div(cls='metadata-item'):
                        div('Scratch Version', cls='metadata-label')
                        div(project.meta.semver)
                    with div(cls='metadata-item'):
                        div('VM Version', cls='metadata-label')
                        div(project.meta.vm)
            
            # Statistics Section
            with div(cls='section', id='statistics'):
                h2('Statistics')
                with div(cls='statistics'):
                    with div(cls='stat-card'):
                        div('Sprites', cls='stat-label')
                        div(str(project.count_sprites()), cls='stat-value')
                    with div(cls='stat-card'):
                        div('Total Blocks', cls='stat-label')
                        div(str(project.count_blocks()), cls='stat-value')
                    with div(cls='stat-card'):
                        div('Cloud Variables', cls='stat-label')
                        div(str(project.count_cloud_variables()), cls='stat-value')
                    with div(cls='stat-card'):
                        div('Global Variables', cls='stat-label')
                        div(str(project.count_global_variables()), cls='stat-value')
                    with div(cls='stat-card'):
                        div('Sprite Variables', cls='stat-label')
                        div(str(project.count_sprite_variables()), cls='stat-value')
                    with div(cls='stat-card'):
                        div('Lists', cls='stat-label')
                        div(str(len(project.get_all_lists())), cls='stat-value')
                    with div(cls='stat-card'):
                        div('Messages', cls='stat-label')
                        div(str(project.count_broadcasts()), cls='stat-value')
                    with div(cls='stat-card'):
                        div('Custom Blocks', cls='stat-label')
                        div(str(project.count_custom_blocks()), cls='stat-value')
                    with div(cls='stat-card'):
                        div('Clones', cls='stat-label')
                        div(str(project.count_clones()), cls='stat-value')
            
            # Extensions Section
            if project.extensions:
                with div(cls='section', id='extensions'):
                    h2('Extensions Used')
                    with div(cls='extensions'):
                        for ext in project.extensions:
                            div(f'🔌 {ext}', cls='extension')
            
            # Stage Section
            stage = project.stage
            if stage:
                with div(cls='section', id='stage'):
                    h2('🎭 Stage')
                    with div(cls='sprite'):
                        with div(cls='sprite-header'):
                            div(stage.name, cls='sprite-name')
                        
                        with div(cls='sprite-props'):
                            with div(cls='prop'):
                                div('Costumes', cls='prop-label')
                                div(str(len(stage.costumes)), cls='prop-value')
                            with div(cls='prop'):
                                div('Sounds', cls='prop-label')
                                div(str(len(stage.sounds)), cls='prop-value')
                            with div(cls='prop'):
                                div('Variables', cls='prop-label')
                                div(str(len(stage.variables)), cls='prop-value')
                            with div(cls='prop'):
                                div('Lists', cls='prop-label')
                                div(str(len(stage.lists)), cls='prop-value')
                            with div(cls='prop'):
                                div('Blocks', cls='prop-label')
                                div(str(len(stage.blocks)), cls='prop-value')
                        
                        # Stage costumes (backdrops)
                        if stage.costumes:
                            h3('Backdrops')
                            with div(cls='assets'):
                                for costume in stage.costumes:
                                    thumb = costume_thumbnails.get(costume.md5ext, '')
                                    if thumb:
                                        with div(cls='asset'):
                                            # Use CDN URL if standalone, else local path
                                            src_url = thumb if standalone else f'{output_name}/{thumb}'
                                            img(src=src_url, alt=costume.name)
                                            div(costume.name, cls='asset-name')
                        
                        # Stage sounds
                        if stage.sounds:
                            h3('Sounds')
                            with div(cls='assets'):
                                for sound in stage.sounds:
                                    if sound.md5ext in sound_files:
                                        with div(cls='asset'):
                                            div(f'🔊 {sound.name}', cls='asset-name')
                                            with audio(controls=True, cls='audio-player'):
                                                # Use CDN URL if standalone, else local path
                                                src_url = sound_files[sound.md5ext] if standalone else f'{output_name}/{sound.md5ext}'
                                                source(src=src_url, type=f'audio/{sound.dataFormat}')
                        
                        # Stage variables
                        if stage.variables:
                            h3('Variables')
                            with div(cls='variables-section'):
                                for var_id, var_data in stage.variables.items():
                                    var_name = var_data[0]
                                    var_value = var_data[1]
                                    is_cloud = len(var_data) == 3 and var_data[2] == True
                                    with div(cls='variable'):
                                        cloud_icon = '☁️ ' if is_cloud else ''
                                        div(f'{cloud_icon}{var_name}', cls='variable-name', escape=False)
                                        div(str(var_value), cls='variable-value')
                        
                        # Stage lists
                        if stage.lists:
                            h3('Lists')
                            with div(cls='lists-section'):
                                for list_id, list_data in stage.lists.items():
                                    list_name = list_data[0]
                                    list_values = list_data[1] if len(list_data) > 1 else []
                                    with div(cls='list'):
                                        div(f'{list_name} ({len(list_values)} items)', cls='list-name')
                                        if list_values:
                                            with div(cls='list-values'):
                                                for i, value in enumerate(list_values[:10], 1):  # Show first 10 items
                                                    div(f'{i}. {value}', cls='list-item')
                                                if len(list_values) > 10:
                                                    div(f'... and {len(list_values) - 10} more', cls='list-more')
                        
                        # Stage messages (broadcasts)
                        if stage.broadcasts:
                            h3('Messages')
                            with div(cls='messages-section'):
                                for broadcast_id, message_name in stage.broadcasts.items():
                                    with div(cls='message'):
                                        div('📢 ' + message_name, cls='message-name', escape=False)
                        
                        # Stage scripts
                        if stage.blocks:
                            scripts = target_to_scratchblocks(stage)
                            if scripts:
                                h3('Scripts')
                                with div(cls='scripts-section'):
                                    # Combine all scripts into a single pre.blocks element
                                    # Scripts are separated by blank lines
                                    combined_scripts = '\n\n'.join(scripts)
                                    pre(combined_scripts, cls='blocks')
            
            # Sprites Section
            sprites = project.sprites
            if sprites:
                with div(cls='section', id='sprites'):
                    h2('🎮 Sprites')
                    for sprite in sprites:
                        # Create valid ID from sprite name
                        sprite_id = f"sprite-{sprite.name.lower().replace(' ', '-')}"
                        with div(cls='sprite', id=sprite_id):
                            with div(cls='sprite-header'):
                                div(sprite.name, cls='sprite-name')
                            
                            with div(cls='sprite-props'):
                                with div(cls='prop'):
                                    div('Position', cls='prop-label')
                                    div(f'({round(sprite.x)}, {round(sprite.y)})', cls='prop-value')
                                with div(cls='prop'):
                                    div('Size', cls='prop-label')
                                    div(f'{sprite.size}%', cls='prop-value')
                                with div(cls='prop'):
                                    div('Direction', cls='prop-label')
                                    div(f'{round(sprite.direction)}°', cls='prop-value')
                                with div(cls='prop'):
                                    div('Visible', cls='prop-label')
                                    div('Yes' if sprite.visible else 'No', cls='prop-value')
                                with div(cls='prop'):
                                    div('Rotation Style', cls='prop-label')
                                    div(sprite.rotationStyle or 'all around', cls='prop-value')
                                with div(cls='prop'):
                                    div('Draggable', cls='prop-label')
                                    div('Yes' if sprite.draggable else 'No', cls='prop-value')
                            
                            with div(cls='blocks-count'):
                                div(f'📦 {len(sprite.blocks)} blocks | '
                                    f'🎨 {len(sprite.costumes)} costumes | '
                                    f'🔊 {len(sprite.sounds)} sounds', escape=False)
                            
                            # Sprite costumes
                            if sprite.costumes:
                                h3('Costumes')
                                with div(cls='assets'):
                                    for costume in sprite.costumes:
                                        thumb = costume_thumbnails.get(costume.md5ext, '')
                                        if thumb:
                                            with div(cls='asset'):
                                                # Use CDN URL if standalone, else local path
                                                src_url = thumb if standalone else f'{output_name}/{thumb}'
                                                img(src=src_url, alt=costume.name)
                                                div(costume.name, cls='asset-name')
                            
                            # Sprite sounds
                            if sprite.sounds:
                                h3('Sounds')
                                with div(cls='assets'):
                                    for sound in sprite.sounds:
                                        if sound.md5ext in sound_files:
                                            with div(cls='asset'):
                                                div(f'🔊 {sound.name}', cls='asset-name')
                                                with audio(controls=True, cls='audio-player'):
                                                    # Use CDN URL if standalone, else local path
                                                    src_url = sound_files[sound.md5ext] if standalone else f'{output_name}/{sound.md5ext}'
                                                    source(src=src_url, type=f'audio/{sound.dataFormat}')
                            
                            # Sprite variables
                            if sprite.variables:
                                h3('Variables')
                                with div(cls='variables-section'):
                                    for var_id, var_data in sprite.variables.items():
                                        var_name = var_data[0]
                                        var_value = var_data[1]
                                        with div(cls='variable'):
                                            div(var_name, cls='variable-name')
                                            div(str(var_value), cls='variable-value')
                            
                            # Sprite lists
                            if sprite.lists:
                                h3('Lists')
                                with div(cls='lists-section'):
                                    for list_id, list_data in sprite.lists.items():
                                        list_name = list_data[0]
                                        list_values = list_data[1] if len(list_data) > 1 else []
                                        with div(cls='list'):
                                            div(f'{list_name} ({len(list_values)} items)', cls='list-name')
                                            if list_values:
                                                with div(cls='list-values'):
                                                    for i, value in enumerate(list_values[:10], 1):  # Show first 10 items
                                                        div(f'{i}. {value}', cls='list-item')
                                                    if len(list_values) > 10:
                                                        div(f'... and {len(list_values) - 10} more', cls='list-more')
                            
                            # Sprite messages (broadcasts)
                            if sprite.broadcasts:
                                h3('Messages')
                                with div(cls='messages-section'):
                                    for broadcast_id, message_name in sprite.broadcasts.items():
                                        with div(cls='message'):
                                            div('📢 ' + message_name, cls='message-name', escape=False)
                            
                            # Sprite scripts
                            if sprite.blocks:
                                scripts = target_to_scratchblocks(sprite)
                                if scripts:
                                    h3('Scripts')
                                    with div(cls='scripts-section'):
                                        # Combine all scripts into a single pre.blocks element
                                        # Scripts are separated by blank lines
                                        combined_scripts = '\n\n'.join(scripts)
                                        pre(combined_scripts, cls='blocks')
    
    # Add scratchblocks JavaScript at the end of body
    with doc:
        script(src='https://cdn.jsdelivr.net/npm/scratchblocks@3.6.4/build/scratchblocks.min.js')
        with script():
            raw("""
        // Render blocks immediately - script tag is at end of body so DOM is ready
        scratchblocks.renderMatching('pre.blocks', {
            style: 'scratch3',
            scale: 0.675
        });
        
        // Sidebar navigation highlighting with scroll tracking
        document.addEventListener('DOMContentLoaded', function() {
            const sections = document.querySelectorAll('.section[id], .sprite[id]');
            const navLinks = document.querySelectorAll('.sidebar-nav a');
            
            // Create a map of section IDs to nav links
            const linkMap = {};
            navLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href && href.startsWith('#')) {
                    const id = href.substring(1);
                    linkMap[id] = link;
                }
            });
            
            function updateActiveLinks() {
                // Remove all active classes
                navLinks.forEach(link => link.classList.remove('active'));
                
                // Find which section is currently at the top of the viewport
                // We check from top to bottom and highlight the last section whose top is above viewport top + 150px
                let currentSection = null;
                const scrollOffset = 150; // pixels from top of viewport
                
                sections.forEach(section => {
                    const rect = section.getBoundingClientRect();
                    // If the section's top is above our scroll offset, it could be the current section
                    if (rect.top <= scrollOffset) {
                        currentSection = section;
                    }
                });
                
                let activeLinkToScroll = null;
                
                if (currentSection) {
                    const id = currentSection.id;
                    
                    // Handle sprite sub-items (sprite-xxx)
                    if (id.startsWith('sprite-')) {
                        // Activate the individual sprite link (priority for scrolling)
                        if (linkMap[id]) {
                            linkMap[id].classList.add('active');
                            activeLinkToScroll = linkMap[id];
                        }
                        // Also activate the main Sprites link
                        if (linkMap['sprites']) {
                            linkMap['sprites'].classList.add('active');
                        }
                        
                        // Ensure sprite subnav is expanded
                        const spriteSubnav = document.getElementById('sprite-subnav');
                        if (spriteSubnav) {
                            spriteSubnav.classList.add('expanded');
                        }
                    } else {
                        // Activate the section link
                        if (linkMap[id]) {
                            linkMap[id].classList.add('active');
                            activeLinkToScroll = linkMap[id];
                        }
                        
                        // If it's the sprites section, expand the subnav
                        if (id === 'sprites') {
                            const spriteSubnav = document.getElementById('sprite-subnav');
                            if (spriteSubnav) {
                                spriteSubnav.classList.add('expanded');
                            }
                        }
                    }
                }
                
                // Scroll the active link into view in the sidebar
                if (activeLinkToScroll) {
                    const sidebar = document.querySelector('.sidebar');
                    if (sidebar) {
                        const linkRect = activeLinkToScroll.getBoundingClientRect();
                        const sidebarRect = sidebar.getBoundingClientRect();
                        
                        // Check if link is outside the visible sidebar area
                        if (linkRect.top < sidebarRect.top || linkRect.bottom > sidebarRect.bottom) {
                            activeLinkToScroll.scrollIntoView({
                                behavior: 'smooth',
                                block: 'center'
                            });
                        }
                    }
                }
            }
            
            // Update on scroll with throttling
            let scrollTimeout;
            window.addEventListener('scroll', function() {
                if (scrollTimeout) {
                    window.cancelAnimationFrame(scrollTimeout);
                }
                scrollTimeout = window.requestAnimationFrame(updateActiveLinks);
            });
            
            // Initial update
            updateActiveLinks();
            // Initial update
            updateActiveLinks();
            
            // Smooth scroll for anchor links
            navLinks.forEach(link => {
                link.addEventListener('click', function(e) {
                    const href = this.getAttribute('href');
                    if (href && href.startsWith('#')) {
                        e.preventDefault();
                        const target = document.querySelector(href);
                        if (target) {
                            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                });
            });
        });
        """)
    
    return str(doc)
