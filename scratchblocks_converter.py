"""Convert Scratch blocks to scratchblocks notation."""

from typing import Any, Dict, List, Optional
from models.project import Block, Target


# Drum number to name mapping for music extension
DRUM_NAMES = {
    "1": "Snare Drum (1)",
    "2": "Bass Drum (2)",
    "3": "Side Stick (3)",
    "4": "Crash Cymbal (4)",
    "5": "Open Hi-Hat (5)",
    "6": "Closed Hi-Hat (6)",
    "7": "Tambourine (7)",
    "8": "Hand Clap (8)",
    "9": "Claves (9)",
    "10": "Wood Block (10)",
    "11": "Cowbell (11)",
    "12": "Triangle (12)",
    "13": "Bongo (13)",
    "14": "Conga (14)",
    "15": "Cabasa (15)",
    "16": "Guiro (16)",
    "17": "Vibraslap (17)",
    "18": "Cuica (18)",
}

# Instrument number to name mapping for music extension
INSTRUMENT_NAMES = {
    "1": "Piano (1)",
    "2": "Electric Piano (2)",
    "3": "Organ (3)",
    "4": "Guitar (4)",
    "5": "Electric Guitar (5)",
    "6": "Bass (6)",
    "7": "Pizzicato (7)",
    "8": "Cello (8)",
    "9": "Trombone (9)",
    "10": "Clarinet (10)",
    "11": "Saxophone (11)",
    "12": "Flute (12)",
    "13": "Wooden Flute (13)",
    "14": "Bassoon (14)",
    "15": "Choir (15)",
    "16": "Vibraphone (16)",
    "17": "Music Box (17)",
    "18": "Steel Drum (18)",
    "19": "Marimba (19)",
    "20": "Synth Lead (20)",
    "21": "Synth Pad (21)",
}

# Pen color parameter mapping for pen extension
PEN_COLOR_PARAM_NAMES = {
    "color": "color",
    "saturation": "saturation",
    "brightness": "brightness",
    "transparency": "transparency",
}

# Face sensing part mapping for face sensing extension
FACE_PART_NAMES = {
    "0": "nose (0)",
    "1": "eyes (1)",
    "2": "mouth (2)",
    "3": "left eye (3)",
    "4": "right eye (4)",
    "5": "left ear (5)",
    "6": "right ear (6)",
    "7": "chin (7)",
}

# Face sensing direction mapping for face sensing extension
FACE_DIRECTION_NAMES = {
    "left": "left",
    "right": "right",
}

# Text to speech voice mapping for text to speech extension
TEXT2SPEECH_VOICES = {
    "ALTO": "alto",
    "TENOR": "tenor",
    "SQUEAK": "squeak",
    "GIANT": "giant",
    "KITTEN": "kitten",
}

# Text to speech language mapping for text to speech extension
# Using common language codes that Scratch supports
TEXT2SPEECH_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh-cn": "Chinese (Mandarin)",
    "pt-br": "Portuguese (Brazilian)",
    "ja": "Japanese",
    "de": "German",
    "hi": "Hindi",
    "it": "Italian",
    "ko": "Korean",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese (European)",
    "ru": "Russian",
    "tr": "Turkish",
    "ar": "Arabic",
    "is": "Icelandic",
    "nb": "Norwegian",
    "ro": "Romanian",
    "sv": "Swedish",
    "cy": "Welsh",
}

# Block shape categorization for dynamic bracket handling
# Boolean blocks use <> brackets when used as inputs
BOOLEAN_BLOCKS = {
    "sensing_touchingobject",
    "sensing_touchingcolor",
    "sensing_coloristouchingcolor",
    "sensing_keypressed",
    "sensing_mousedown",
    "operator_gt",
    "operator_lt",
    "operator_equals",
    "operator_and",
    "operator_or",
    "operator_not",
    "operator_contains",
    "data_listcontainsitem",
    "faceSensing_faceIsDetected",
}

# Reporter blocks use () brackets when used as inputs
# This includes all blocks that return values but aren't booleans
# Most blocks with () in their template are reporters

# Menu blocks are internal and should not have brackets added
# They are placeholders for dropdown values
MENU_BLOCKS = {
    "sensing_touchingobjectmenu",
    "motion_pointtowards_menu",
    "motion_goto_menu",
    "motion_glideto_menu",
    "looks_costume",
    "looks_backdrops",
    "sound_sounds_menu",
    "event_broadcast_menu",
    "control_create_clone_of_menu",
    "sensing_of_object_menu",
    "sensing_distancetomenu",
    "sensing_keyoptions",
    "music_menu_DRUM",
    "music_menu_INSTRUMENT",
    "note",
    "pen_menu_colorParam",
    "videoSensing_menu_ATTRIBUTE",
    "videoSensing_menu_SUBJECT",
    "videoSensing_menu_VIDEO_STATE",
    "text2speech_menu_voices",
    "text2speech_menu_languages",
    "translate_menu_languages",
}

# Field names that are dropdown menus and need [value v] format
DROPDOWN_FIELDS = {
    "TO", "TOWARDS", "STYLE", "COSTUME", "BACKDROP", "EFFECT",
    "FRONT_BACK", "FORWARD_BACKWARD", "NUMBER_NAME", "SOUND_MENU",
    "KEY_OPTION", "WHENGREATERTHANMENU", "BROADCAST_OPTION", "BROADCAST_INPUT",
    "STOP_OPTION", "CLONE_OPTION", "TOUCHINGOBJECTMENU", "DISTANCETOMENU",
    "DRAG_MODE", "PROPERTY", "OBJECT", "CURRENTMENU", "OPERATOR",
    "VARIABLE", "LIST", "DRUM", "INSTRUMENT",
    "ATTRIBUTE", "SUBJECT", "VIDEO_STATE", "PART", "DIRECTION",
    "VOICE", "LANGUAGE", "voices", "languages",
}

# Opcode to scratchblocks notation mapping (based on scratch-opcodes-list.html)
OPCODE_MAP = {
    # Motion blocks
    "motion_movesteps": "move {STEPS} steps",
    "motion_turnright": "turn cw {DEGREES} degrees",
    "motion_turnleft": "turn ccw {DEGREES} degrees",
    "motion_goto": "go to {TO}",
    "motion_gotoxy": "go to x: {X} y: {Y}",
    "motion_glideto": "glide {SECS} secs to {TO}",
    "motion_glidesecstoxy": "glide {SECS} secs to x: {X} y: {Y}",
    "motion_pointindirection": "point in direction {DIRECTION}",
    "motion_pointtowards": "point towards {TOWARDS}",
    "motion_changexby": "change x by {DX}",
    "motion_setx": "set x to {X}",
    "motion_changeyby": "change y by {DY}",
    "motion_sety": "set y to {Y}",
    "motion_ifonedgebounce": "if on edge, bounce",
    "motion_setrotationstyle": "set rotation style {STYLE}",
    "motion_xposition": "(x position)",
    "motion_yposition": "(y position)",
    "motion_direction": "(direction)",
    
    # Looks blocks
    "looks_sayforsecs": "say {MESSAGE} for {SECS} seconds",
    "looks_say": "say {MESSAGE}",
    "looks_thinkforsecs": "think {MESSAGE} for {SECS} seconds",
    "looks_think": "think {MESSAGE}",
    "looks_switchcostumeto": "switch costume to {COSTUME}",
    "looks_nextcostume": "next costume",
    "looks_switchbackdropto": "switch backdrop to {BACKDROP}",
    "looks_nextbackdrop": "next backdrop",
    "looks_changesizeby": "change size by {CHANGE}",
    "looks_setsizeto": "set size to {SIZE}%",
    "looks_changeeffectby": "change {EFFECT} effect by {CHANGE}",
    "looks_seteffectto": "set {EFFECT} effect to {VALUE}",
    "looks_cleargraphiceffects": "clear graphic effects",
    "looks_show": "show",
    "looks_hide": "hide",
    "looks_gotofrontback": "go to {FRONT_BACK} layer",
    "looks_goforwardbackwardlayers": "go {FORWARD_BACKWARD} {NUM} layers",
    "looks_costumenumbername": "(costume {NUMBER_NAME})",
    "looks_backdropnumbername": "(backdrop {NUMBER_NAME})",
    "looks_size": "(size)",
    
    # Sound blocks
    "sound_playuntildone": "play sound {SOUND_MENU} until done",
    "sound_play": "start sound {SOUND_MENU}",
    "sound_stopallsounds": "stop all sounds",
    "sound_changeeffectby": "change {EFFECT} effect by {VALUE} :: sound",
    "sound_seteffectto": "set {EFFECT} effect to {VALUE} :: sound",
    "sound_cleareffects": "clear sound effects",
    "sound_changevolumeby": "change volume by {VOLUME}",
    "sound_setvolumeto": "set volume to {VOLUME}%",
    "sound_volume": "(volume)",
    
    # Events blocks
    "event_whenflagclicked": "when green flag clicked",
    "event_whenkeypressed": "when {KEY_OPTION} key pressed",
    "event_whenthisspriteclicked": "when this sprite clicked",
    "event_whenstageclicked": "when stage clicked",
    "event_whenbackdropswitchesto": "when backdrop switches to {BACKDROP}",
    "event_whengreaterthan": "when {WHENGREATERTHANMENU} > {VALUE}",
    "event_whenbroadcastreceived": "when I receive {BROADCAST_OPTION}",
    "event_broadcast": "broadcast {BROADCAST_INPUT}",
    "event_broadcastandwait": "broadcast {BROADCAST_INPUT} and wait",
    
    # Control blocks
    "control_wait": "wait {DURATION} seconds",
    "control_repeat": "repeat {TIMES}",
    "control_forever": "forever",
    "control_if": "if {CONDITION} then",
    "control_if_else": "if {CONDITION} then\nelse",
    "control_wait_until": "wait until {CONDITION}",
    "control_repeat_until": "repeat until {CONDITION}",
    "control_stop": "stop {STOP_OPTION}",
    "control_start_as_clone": "when I start as a clone",
    "control_create_clone_of": "create clone of {CLONE_OPTION}",
    "control_delete_this_clone": "delete this clone",
    
    # Sensing blocks
    "sensing_touchingobject": "<touching {TOUCHINGOBJECTMENU}?> ",
    "sensing_touchingcolor": "<touching color {COLOR}?> ",
    "sensing_coloristouchingcolor": "<color {COLOR} is touching {COLOR2}?>",
    "sensing_distanceto": "(distance to {DISTANCETOMENU})",
    "sensing_askandwait": "ask {QUESTION} and wait",
    "sensing_answer": "(answer)",
    "sensing_keypressed": "<key {KEY_OPTION} pressed?>",
    "sensing_mousedown": "<mouse down?>",
    "sensing_mousex": "(mouse x)",
    "sensing_mousey": "(mouse y)",
    "sensing_setdragmode": "set drag mode {DRAG_MODE}",
    "sensing_loudness": "(loudness)",
    "sensing_timer": "(timer)",
    "sensing_resettimer": "reset timer",
    "sensing_of": "({PROPERTY} of {OBJECT})",
    "sensing_current": "(current {CURRENTMENU})",
    "sensing_dayssince2000": "(days since 2000)",
    "sensing_username": "(username)",
    
    # Operators blocks
    "operator_add": "({NUM1} + {NUM2})",
    "operator_subtract": "({NUM1} - {NUM2})",
    "operator_multiply": "({NUM1} * {NUM2})",
    "operator_divide": "({NUM1} / {NUM2})",
    "operator_random": "(pick random {FROM} to {TO})",
    "operator_gt": "<{OPERAND1} > {OPERAND2}>",
    "operator_lt": "<{OPERAND1} < {OPERAND2}>",
    "operator_equals": "<{OPERAND1} = {OPERAND2}>",
    "operator_and": "<{OPERAND1} and {OPERAND2}>",
    "operator_or": "<{OPERAND1} or {OPERAND2}>",
    "operator_not": "<not {OPERAND}>",
    "operator_join": "(join {STRING1} {STRING2})",
    "operator_letter_of": "(letter {LETTER} of {STRING})",
    "operator_length": "(length of {STRING})",
    "operator_contains": "<{STRING1} contains {STRING2}?>",
    "operator_mod": "({NUM1} mod {NUM2})",
    "operator_round": "(round {NUM})",
    "operator_mathop": "({OPERATOR} of {NUM} :: operators)",
    
    # Variables blocks
    "data_setvariableto": "set {VARIABLE} to {VALUE}",
    "data_changevariableby": "change {VARIABLE} by {VALUE}",
    "data_showvariable": "show variable {VARIABLE}",
    "data_hidevariable": "hide variable {VARIABLE}",
    
    # List blocks
    "data_addtolist": "add {ITEM} to {LIST}",
    "data_deleteoflist": "delete {INDEX} of {LIST}",
    "data_deletealloflist": "delete all of {LIST}",
    "data_insertatlist": "insert {ITEM} at {INDEX} of {LIST}",
    "data_replaceitemoflist": "replace item {INDEX} of {LIST} with {ITEM}",
    "data_itemoflist": "(item {INDEX} of {LIST})",
    "data_itemnumoflist": "(item # of {ITEM} in {LIST})",
    "data_lengthoflist": "(length of {LIST})",
    "data_listcontainsitem": "<{LIST} contains {ITEM}?>",
    "data_showlist": "show list {LIST}",
    "data_hidelist": "hide list {LIST}",
    
    # My Blocks (custom)
    "procedures_definition": "define {PROCCODE}",
    "procedures_call": "{PROCCODE}",
    "argument_reporter_string_number": "({VALUE})",
    "argument_reporter_boolean": "<{VALUE}>",
    
    # Menu blocks (internal reporters) - these should just return the value without wrappers
    "sensing_touchingobjectmenu": "{TOUCHINGOBJECTMENU}",
    "motion_pointtowards_menu": "{TOWARDS}",
    "motion_goto_menu": "{TO}",
    "motion_glideto_menu": "{TO}",
    "looks_costume": "{COSTUME}",
    "looks_backdrops": "{BACKDROP}",
    "sound_sounds_menu": "{SOUND_MENU}",
    "event_broadcast_menu": "{BROADCAST_OPTION}",
    "control_create_clone_of_menu": "{CLONE_OPTION}",
    "sensing_of_object_menu": "{OBJECT}",
    "sensing_distancetomenu": "{DISTANCETOMENU}",
    "sensing_keyoptions": "{KEY_OPTION}",
    
    # Music extension blocks
    "music_playDrumForBeats": "play drum {DRUM} for {BEATS} beats",
    "music_restForBeats": "rest for {BEATS} beats",
    "music_playNoteForBeats": "play note {NOTE} for {BEATS} beats",
    "music_setInstrument": "set instrument to {INSTRUMENT}",
    "music_setTempo": "set tempo to {TEMPO}",
    "music_changeTempo": "change tempo by {TEMPO}",
    "music_getTempo": "(tempo)",
    
    # Music menu blocks - these should just return the value without wrappers
    "music_menu_DRUM": "{DRUM}",
    "music_menu_INSTRUMENT": "{INSTRUMENT}",
    "note": "[{NOTE}]",
    
    # Pen extension blocks
    "pen_clear": "erase all",
    "pen_stamp": "stamp",
    "pen_penDown": "pen down",
    "pen_penUp": "pen up",
    "pen_setPenColorToColor": "set pen color to {COLOR}",
    "pen_changePenColorParamBy": "change pen {COLOR_PARAM} by {VALUE}",
    "pen_setPenColorParamTo": "set pen {COLOR_PARAM} to {VALUE}",
    "pen_changePenSizeBy": "change pen size by {SIZE}",
    "pen_setPenSizeTo": "set pen size to {SIZE}",
    
    # Pen menu blocks
    "pen_menu_colorParam": "{colorParam}",
    
    # Video Sensing extension blocks
    "videoSensing_whenMotionGreaterThan": "when video motion > {REFERENCE}",
    "videoSensing_videoOn": "(video {ATTRIBUTE} on {SUBJECT})",
    "videoSensing_videoToggle": "turn video {VIDEO_STATE}",
    "videoSensing_setVideoTransparency": "set video transparency to {TRANSPARENCY}%",
    
    # Video Sensing menu blocks
    "videoSensing_menu_ATTRIBUTE": "{ATTRIBUTE}",
    "videoSensing_menu_SUBJECT": "{SUBJECT}",
    "videoSensing_menu_VIDEO_STATE": "{VIDEO_STATE}",
    
    # Face Sensing extension blocks
    "faceSensing_whenFaceDetected": "when face is detected::#00aa00",
    "faceSensing_whenTilted": "when head tilted {DIRECTION}::#00aa00",
    "faceSensing_whenSpriteTouchesPart": "when this sprite touches {PART}::#00aa00",
    "faceSensing_goToPart": "go to {PART}::#00aa00",
    "faceSensing_pointInFaceTiltDirection": "point in face tilt direction::#00aa00",
    "faceSensing_setSizeToFaceSize": "set size to face size::#00aa00",
    "faceSensing_faceIsDetected": "<face is detected?::#00aa00>",
    "faceSensing_faceTilt": "(face tilt::#00aa00)",
    "faceSensing_faceSize": "(face size::#00aa00)",
    
    # Text to Speech extension blocks
    "text2speech_speakAndWait": "speak {WORDS}",
    "text2speech_setVoice": "set voice to {VOICE}",
    "text2speech_setLanguage": "set language to {LANGUAGE}",
    
    # Text to Speech menu blocks
    "text2speech_menu_voices": "{voices}",
    "text2speech_menu_languages": "{languages}",
    
    # Translate extension blocks
    "translate_getTranslate": "(translate {WORDS} to {LANGUAGE})",
    "translate_getViewerLanguage": "(language)",
    
    # Translate menu blocks
    "translate_menu_languages": "{languages}",
}

def get_input_value(block: Block, input_name: str, blocks: Dict[str, Block]) -> str:
    """Extract input value from a block and wrap with appropriate brackets.
    
    Brackets are determined by the value type:
    - Literals (numbers, text) use []
    - Reporter blocks use ()
    - Boolean blocks use <>
    - Menu blocks return unwrapped values (will be wrapped with [v] in templates)
    """
    if not block.inputs or input_name not in block.inputs:
        return "[?]"
    
    input_data = block.inputs[input_name]
    
    # Input format: [input_type, value, ...] or [input_type, value]
    if not isinstance(input_data, list) or len(input_data) < 2:
        return "[?]"
    
    input_type = input_data[0]
    value = input_data[1]
    
    # Type 1: Shadow (dropdown/primitive) - [type, [shadow_type, value]]
    # Type 2: No shadow (block reference or primitive) - [type, value]  
    # Type 3: Obscured shadow - [type, block_id, [shadow_type, value]]
    
    # Check if it's a block reference (string)
    if isinstance(value, str):
        # It's a block ID reference
        if value in blocks:
            referenced_block = blocks[value]
            scratchblock = block_to_scratchblocks(referenced_block, blocks)
            
            # Determine bracket type based on the referenced block's opcode
            if referenced_block.opcode in BOOLEAN_BLOCKS:
                # Check if already has outer <> brackets
                if scratchblock.strip().startswith("<") and scratchblock.strip().endswith(">"):
                    return scratchblock
                return f"<{scratchblock}>"
            elif referenced_block.opcode in MENU_BLOCKS:
                # Menu blocks should not be wrapped - they return values for dropdowns
                return scratchblock
            else:
                # Reporter blocks and others use ()
                # Check if already has outer () brackets
                if scratchblock.strip().startswith("(") and scratchblock.strip().endswith(")"):
                    return scratchblock
                return f"({scratchblock})"
        # Unknown block reference
        return f"[{value}]"
    
    # Check if it's a primitive value [type, value]
    if isinstance(value, list) and len(value) >= 2:
        primitive_type = value[0]
        primitive_value = value[1]
        
        # Type 4-8 are primitives (number, positive number, angle, color, text, broadcast, variable, list)
        # Type 11 is a dropdown menu value
        if primitive_type in [4, 5, 6, 7, 8, 9, 10, 12, 13]:
            # Special handling for pen color parameter field menus
            if input_name == "colorParam" and str(primitive_value) in PEN_COLOR_PARAM_NAMES:
                return PEN_COLOR_PARAM_NAMES[str(primitive_value)]
            # Primitive literals use []
            return f"[{primitive_value}]"
        elif primitive_type == 11:
            # Type 11 is a dropdown menu - add [value v] format and strip underscores
            menu_value = str(primitive_value)
            if menu_value.startswith("_") and menu_value.endswith("_"):
                menu_value = menu_value.strip("_")
            return f"[{menu_value} v]"
    
    # For obscured shadows, try the third element
    if len(input_data) >= 3 and isinstance(input_data[2], list):
        shadow = input_data[2]
        if len(shadow) >= 2:
            # Special handling for pen color parameter in obscured shadows
            if input_name == "colorParam" and str(shadow[1]) in PEN_COLOR_PARAM_NAMES:
                return PEN_COLOR_PARAM_NAMES[str(shadow[1])]
            # Shadow values are literals, use []
            return f"[{shadow[1]}]"
    
    return "[?]"


def get_field_value(block: Block, field_name: str) -> str:
    """Extract field value from a block and wrap with [value v] if it's a dropdown."""
    if not block.fields or field_name not in block.fields:
        return "?"
    
    field_data = block.fields[field_name]
    value = str(field_data[0]) if isinstance(field_data, list) and len(field_data) > 0 else str(field_data)
    
    # Convert drum numbers to names for music extension
    if field_name == "DRUM" and value in DRUM_NAMES:
        value = DRUM_NAMES[value]
    
    # Convert instrument numbers to names for music extension
    if field_name == "INSTRUMENT" and value in INSTRUMENT_NAMES:
        value = INSTRUMENT_NAMES[value]
    
    # Convert pen color parameter names for pen extension (lowercase field name)
    if field_name == "colorParam" and value in PEN_COLOR_PARAM_NAMES:
        value = PEN_COLOR_PARAM_NAMES[value]
        # Use dropdown format [... v] for all pen color parameters
        return f"[{value} v]"
    
    # Convert face part numbers to names for face sensing extension
    if field_name == "PART" and value in FACE_PART_NAMES:
        value = FACE_PART_NAMES[value]
    
    # Convert face direction for face sensing extension
    if field_name == "DIRECTION" and value in FACE_DIRECTION_NAMES:
        value = FACE_DIRECTION_NAMES[value]
    
    # Convert voice names for text to speech extension
    if field_name == "voices" and value in TEXT2SPEECH_VOICES:
        value = TEXT2SPEECH_VOICES[value]
    
    # Convert language codes for text to speech extension
    if field_name == "languages" and value in TEXT2SPEECH_LANGUAGES:
        value = TEXT2SPEECH_LANGUAGES[value]
    
    # Convert specific uppercase field values to lowercase for scratchblocks
    uppercase_to_lowercase = [
        "BRIGHTNESS", "COLOR", "DATE", "DAYOFWEEK", "FISHEYE", "GHOST", 
        "HOUR", "LOUDNESS", "MINUTE", "MONTH", "MOSAIC", "PAN", 
        "PITCH", "PIXELATE", "SECOND", "TIMER", "WHIRL", "YEAR"
    ]
    if value in uppercase_to_lowercase:
        value = value.lower()
    
    # Strip underscores from special dropdown values like _random_ and _mouse_
    if value.startswith("_") and value.endswith("_"):
        value = value.strip("_")
    
    # Add [value v] format for dropdown fields
    if field_name in DROPDOWN_FIELDS:
        return f"[{value} v]"
    
    return value


def block_to_scratchblocks(block: Block, blocks: Dict[str, Block], indent: int = 0) -> str:
    """Convert a single block to scratchblocks notation."""
    if block.opcode not in OPCODE_MAP:
        return f"{' ' * indent}// Unknown block: {block.opcode}"
    
    template = OPCODE_MAP[block.opcode]
    
    # Special handling for procedures_definition (custom blocks)
    if block.opcode == "procedures_definition":
        # Get the prototype block referenced by custom_block input
        if block.inputs and "custom_block" in block.inputs:
            custom_block_input = block.inputs["custom_block"]
            if isinstance(custom_block_input, list) and len(custom_block_input) >= 2:
                prototype_id = custom_block_input[1]
                if isinstance(prototype_id, str) and prototype_id in blocks:
                    prototype_block = blocks[prototype_id]
                    # Extract proccode from mutation
                    if hasattr(prototype_block, 'mutation') and prototype_block.mutation:
                        proccode = prototype_block.mutation.get('proccode', '?')
                        # Convert %s and %b to scratchblocks format
                        # %s (string/number) -> (param)
                        # %b (boolean) -> <param>
                        import json
                        argumentnames = json.loads(prototype_block.mutation.get('argumentnames', '[]'))
                        
                        # Replace %s with (name) and %b with <name>
                        result = proccode
                        for arg_name in argumentnames:
                            # Try %s first (string/number parameter)
                            if '%s' in result:
                                result = result.replace('%s', f'({arg_name})', 1)
                            # Try %b (boolean parameter)
                            elif '%b' in result:
                                result = result.replace('%b', f'<{arg_name}>', 1)
                        
                        return f"{' ' * indent}define {result}"
        return f"{' ' * indent}define ?"
    
    # Special handling for procedures_call (calling custom blocks)
    if block.opcode == "procedures_call":
        if hasattr(block, 'mutation') and block.mutation:
            import json
            proccode = block.mutation.get('proccode', '?')
            argumentids = json.loads(block.mutation.get('argumentids', '[]'))
            
            # Replace %s and %b with actual input values
            result = proccode
            for arg_id in argumentids:
                if block.inputs and arg_id in block.inputs:
                    value = get_input_value(block, arg_id, blocks)
                    # Try %s first (string/number parameter)
                    if '%s' in result:
                        result = result.replace('%s', value, 1)
                    # Try %b (boolean parameter)
                    elif '%b' in result:
                        result = result.replace('%b', value, 1)
            
            return f"{' ' * indent}{result}"
        return f"{' ' * indent}?"
    
    # Replace placeholders with actual values
    result = template
    
    # Handle inputs (values in parentheses or angles)
    # Skip SUBSTACK inputs as they are handled separately
    if block.inputs:
        for input_name, input_data in block.inputs.items():
            if input_name in ["SUBSTACK", "SUBSTACK2"]:
                continue
            placeholder = f"{{{input_name}}}"
            if placeholder in result:
                value = get_input_value(block, input_name, blocks)
                result = result.replace(placeholder, value)
    
    # Handle fields (dropdown menus)
    if block.fields:
        for field_name, field_data in block.fields.items():
            placeholder = f"{{{field_name}}}"
            if placeholder in result:
                value = get_field_value(block, field_name)
                result = result.replace(placeholder, value)
    
    # Clean up any remaining placeholders (both UPPERCASE and camelCase)
    import re
    result = re.sub(r'\{[A-Za-z_]+\}', '?', result)
    
    return f"{' ' * indent}{result}"


def get_script_top_blocks(target: Target) -> List[str]:
    """Get IDs of top-level blocks (hat blocks or orphaned stacks)."""
    top_blocks = []
    
    # Find blocks that are not referenced by any other block's "next"
    referenced_as_next = set()
    for block in target.blocks.values():
        if block.next:
            referenced_as_next.add(block.next)
    
    # Top blocks are those not referenced as "next" and have no parent
    for block_id, block in target.blocks.items():
        if block_id not in referenced_as_next and not block.parent:
            top_blocks.append(block_id)
    
    return top_blocks


def script_to_scratchblocks(start_block_id: str, blocks: Dict[str, Block], indent: int = 0) -> str:
    """Convert a script (sequence of connected blocks) to scratchblocks notation."""
    lines = []
    current_id = start_block_id
    
    while current_id:
        if current_id not in blocks:
            break
        
        block = blocks[current_id]
        block_text = block_to_scratchblocks(block, blocks, indent)
        lines.append(block_text)
        
        # Handle C-blocks (control structures with substacks)
        if block.opcode in ["control_repeat", "control_forever", "control_if", 
                            "control_if_else", "control_repeat_until"]:
            # Get substack block ID directly from inputs
            if block.inputs and "SUBSTACK" in block.inputs:
                substack_input = block.inputs["SUBSTACK"]
                substack_id = None
                if isinstance(substack_input, list) and len(substack_input) >= 2:
                    if isinstance(substack_input[1], str):
                        substack_id = substack_input[1]
                
                if substack_id and substack_id in blocks:
                    substack_text = script_to_scratchblocks(substack_id, blocks, indent + 2)
                    lines.append(substack_text)
            
            # Handle else branch for if-else
            if block.opcode == "control_if_else" and block.inputs and "SUBSTACK2" in block.inputs:
                substack2_input = block.inputs["SUBSTACK2"]
                substack2_id = None
                if isinstance(substack2_input, list) and len(substack2_input) >= 2:
                    if isinstance(substack2_input[1], str):
                        substack2_id = substack2_input[1]
                
                if substack2_id and substack2_id in blocks:
                    substack2_text = script_to_scratchblocks(substack2_id, blocks, indent + 2)
                    lines.append(substack2_text)
            
            # Add "end" for C-blocks
            lines.append(f"{' ' * indent}end")
        
        current_id = block.next
    
    return "\n".join(lines)


def target_to_scratchblocks(target: Target) -> List[str]:
    """Convert all scripts in a target to scratchblocks notation."""
    scripts = []
    top_block_ids = get_script_top_blocks(target)
    
    for block_id in top_block_ids:
        script_text = script_to_scratchblocks(block_id, target.blocks)
        if script_text.strip():
            scripts.append(script_text)
    
    return scripts
