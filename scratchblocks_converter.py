"""Convert Scratch blocks to scratchblocks notation."""

from typing import Any, Dict, List, Optional
from models.project import Block, Target


# Opcode to scratchblocks notation mapping (based on scratch-opcodes-list.html)
OPCODE_MAP = {
    # Motion blocks
    "motion_movesteps": "move ({STEPS}) steps",
    "motion_turnright": "turn cw ({DEGREES}) degrees",
    "motion_turnleft": "turn ccw ({DEGREES}) degrees",
    "motion_goto": "go to ({TO})",
    "motion_gotoxy": "go to x: ({X}) y: ({Y})",
    "motion_glideto": "glide ({SECS}) secs to ({TO})",
    "motion_glidesecstoxy": "glide ({SECS}) secs to x: ({X}) y: ({Y})",
    "motion_pointindirection": "point in direction ({DIRECTION})",
    "motion_pointtowards": "point towards ({TOWARDS})",
    "motion_changexby": "change x by ({DX})",
    "motion_setx": "set x to ({X})",
    "motion_changeyby": "change y by ({DY})",
    "motion_sety": "set y to ({Y})",
    "motion_ifonedgebounce": "if on edge, bounce",
    "motion_setrotationstyle": "set rotation style [{STYLE}]",
    "motion_xposition": "(x position)",
    "motion_yposition": "(y position)",
    "motion_direction": "(direction)",
    
    # Looks blocks
    "looks_sayforsecs": "say ({MESSAGE}) for ({SECS}) seconds",
    "looks_say": "say ({MESSAGE})",
    "looks_thinkforsecs": "think ({MESSAGE}) for ({SECS}) seconds",
    "looks_think": "think ({MESSAGE})",
    "looks_switchcostumeto": "switch costume to ({COSTUME})",
    "looks_nextcostume": "next costume",
    "looks_switchbackdropto": "switch backdrop to ({BACKDROP})",
    "looks_nextbackdrop": "next backdrop",
    "looks_changesizeby": "change size by ({CHANGE})",
    "looks_setsizeto": "set size to ({SIZE})%",
    "looks_changeeffectby": "change [{EFFECT}] effect by ({CHANGE})",
    "looks_seteffectto": "set [{EFFECT}] effect to ({VALUE})",
    "looks_cleargraphiceffects": "clear graphic effects",
    "looks_show": "show",
    "looks_hide": "hide",
    "looks_gotofrontback": "go to [{FRONT_BACK}] layer",
    "looks_goforwardbackwardlayers": "go [{FORWARD_BACKWARD}] ({NUM}) layers",
    "looks_costumenumbername": "(costume [{NUMBER_NAME}])",
    "looks_backdropnumbername": "(backdrop [{NUMBER_NAME}])",
    "looks_size": "(size)",
    
    # Sound blocks
    "sound_playuntildone": "play sound ({SOUND_MENU}) until done",
    "sound_play": "start sound ({SOUND_MENU})",
    "sound_stopallsounds": "stop all sounds",
    "sound_changeeffectby": "change [{EFFECT}] effect by ({VALUE}) :: sound",
    "sound_seteffectto": "set [{EFFECT}] effect to ({VALUE}) :: sound",
    "sound_cleareffects": "clear sound effects",
    "sound_changevolumeby": "change volume by ({VOLUME})",
    "sound_setvolumeto": "set volume to ({VOLUME})%",
    "sound_volume": "(volume)",
    
    # Events blocks
    "event_whenflagclicked": "when green flag clicked",
    "event_whenkeypressed": "when [{KEY_OPTION}] key pressed",
    "event_whenthisspriteclicked": "when this sprite clicked",
    "event_whenstageclicked": "when stage clicked",
    "event_whenbackdropswitchesto": "when backdrop switches to [{BACKDROP}]",
    "event_whengreaterthan": "when [{WHENGREATERTHANMENU}] > ({VALUE})",
    "event_whenbroadcastreceived": "when I receive [{BROADCAST_OPTION}]",
    "event_broadcast": "broadcast ({BROADCAST_INPUT})",
    "event_broadcastandwait": "broadcast ({BROADCAST_INPUT}) and wait",
    
    # Control blocks
    "control_wait": "wait ({DURATION}) seconds",
    "control_repeat": "repeat ({TIMES})",
    "control_forever": "forever",
    "control_if": "if <{CONDITION}> then",
    "control_if_else": "if <{CONDITION}> then\nelse",
    "control_wait_until": "wait until <{CONDITION}>",
    "control_repeat_until": "repeat until <{CONDITION}>",
    "control_stop": "stop [{STOP_OPTION}]",
    "control_start_as_clone": "when I start as a clone",
    "control_create_clone_of": "create clone of ({CLONE_OPTION})",
    "control_delete_this_clone": "delete this clone",
    
    # Sensing blocks
    "sensing_touchingobject": "<touching ({TOUCHINGOBJECTMENU})?> ",
    "sensing_touchingcolor": "<touching color ({COLOR})?> ",
    "sensing_coloristouchingcolor": "<color ({COLOR}) is touching ({COLOR2})?>",
    "sensing_distanceto": "(distance to ({DISTANCETOMENU}))",
    "sensing_askandwait": "ask ({QUESTION}) and wait",
    "sensing_answer": "(answer)",
    "sensing_keypressed": "<key ({KEY_OPTION}) pressed?>",
    "sensing_mousedown": "<mouse down?>",
    "sensing_mousex": "(mouse x)",
    "sensing_mousey": "(mouse y)",
    "sensing_setdragmode": "set drag mode [{DRAG_MODE}]",
    "sensing_loudness": "(loudness)",
    "sensing_timer": "(timer)",
    "sensing_resettimer": "reset timer",
    "sensing_of": "([{PROPERTY}] of ({OBJECT}))",
    "sensing_current": "(current [{CURRENTMENU}])",
    "sensing_dayssince2000": "(days since 2000)",
    "sensing_username": "(username)",
    
    # Operators blocks
    "operator_add": "(({NUM1}) + ({NUM2}))",
    "operator_subtract": "(({NUM1}) - ({NUM2}))",
    "operator_multiply": "(({NUM1}) * ({NUM2}))",
    "operator_divide": "(({NUM1}) / ({NUM2}))",
    "operator_random": "(pick random ({FROM}) to ({TO}))",
    "operator_gt": "<({OPERAND1}) > ({OPERAND2})>",
    "operator_lt": "<({OPERAND1}) < ({OPERAND2})>",
    "operator_equals": "<({OPERAND1}) = ({OPERAND2})>",
    "operator_and": "<<{OPERAND1}> and <{OPERAND2}>>",
    "operator_or": "<<{OPERAND1}> or <{OPERAND2}>>",
    "operator_not": "<not <{OPERAND}>>",
    "operator_join": "(join ({STRING1}) ({STRING2}))",
    "operator_letter_of": "(letter ({LETTER}) of ({STRING}))",
    "operator_length": "(length of ({STRING}))",
    "operator_contains": "<({STRING1}) contains ({STRING2})?>",
    "operator_mod": "(({NUM1}) mod ({NUM2}))",
    "operator_round": "(round ({NUM}))",
    "operator_mathop": "([{OPERATOR}] of ({NUM}) :: operators)",
    
    # Variables blocks
    "data_setvariableto": "set [{VARIABLE}] to ({VALUE})",
    "data_changevariableby": "change [{VARIABLE}] by ({VALUE})",
    "data_showvariable": "show variable [{VARIABLE}]",
    "data_hidevariable": "hide variable [{VARIABLE}]",
    
    # List blocks
    "data_addtolist": "add ({ITEM}) to [{LIST}]",
    "data_deleteoflist": "delete ({INDEX}) of [{LIST}]",
    "data_deletealloflist": "delete all of [{LIST}]",
    "data_insertatlist": "insert ({ITEM}) at ({INDEX}) of [{LIST}]",
    "data_replaceitemoflist": "replace item ({INDEX}) of [{LIST}] with ({ITEM})",
    "data_itemoflist": "(item ({INDEX}) of [{LIST}])",
    "data_itemnumoflist": "(item # of ({ITEM}) in [{LIST}])",
    "data_lengthoflist": "(length of [{LIST}])",
    "data_listcontainsitem": "<[{LIST}] contains ({ITEM})?>",
    "data_showlist": "show list [{LIST}]",
    "data_hidelist": "hide list [{LIST}]",
    
    # My Blocks (custom)
    "procedures_definition": "define {PROCCODE}",
    "procedures_call": "{PROCCODE}",
    
    # Menu blocks (internal reporters)
    "sensing_touchingobjectmenu": "({TOUCHINGOBJECTMENU})",
    "motion_pointtowards_menu": "({TOWARDS})",
    "motion_goto_menu": "({TO})",
    "motion_glideto_menu": "({TO})",
    "looks_costume": "({COSTUME})",
    "looks_backdrops": "({BACKDROP})",
    "sound_sounds_menu": "({SOUND_MENU})",
    "event_broadcast_menu": "({BROADCAST_OPTION})",
    "control_create_clone_of_menu": "({CLONE_OPTION})",
    "sensing_of_object_menu": "({OBJECT})",
    "sensing_distancetomenu": "({DISTANCETOMENU})",
    "sensing_keyoptions": "({KEY_OPTION})",
    "sensing_touchingcolor": "({COLOR})",
}

def get_input_value(block: Block, input_name: str, blocks: Dict[str, Block]) -> str:
    """Extract input value from a block."""
    if not block.inputs or input_name not in block.inputs:
        return "?"
    
    input_data = block.inputs[input_name]
    
    # Input format: [input_type, value, ...] or [input_type, value]
    if not isinstance(input_data, list) or len(input_data) < 2:
        return "?"
    
    input_type = input_data[0]
    value = input_data[1]
    
    # Type 1: Shadow (dropdown/primitive) - [type, [shadow_type, value]]
    # Type 2: No shadow (block reference or primitive) - [type, value]  
    # Type 3: Obscured shadow - [type, block_id, [shadow_type, value]]
    
    # Check if it's a block reference (string)
    if isinstance(value, str):
        # It's a block ID reference
        if value in blocks:
            return block_to_scratchblocks(blocks[value], blocks)
        # Unknown block reference
        return value
    
    # Check if it's a primitive value [type, value]
    if isinstance(value, list) and len(value) >= 2:
        primitive_type = value[0]
        primitive_value = value[1]
        
        # Type 4-8 are primitives (number, positive number, angle, color, text, broadcast, variable, list)
        if primitive_type in [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
            return str(primitive_value)
    
    # For obscured shadows, try the third element
    if len(input_data) >= 3 and isinstance(input_data[2], list):
        shadow = input_data[2]
        if len(shadow) >= 2:
            return str(shadow[1])
    
    return "?"


def get_field_value(block: Block, field_name: str) -> str:
    """Extract field value from a block."""
    if not block.fields or field_name not in block.fields:
        return "?"
    
    field_data = block.fields[field_name]
    if isinstance(field_data, list) and len(field_data) > 0:
        return str(field_data[0])
    return str(field_data)


def block_to_scratchblocks(block: Block, blocks: Dict[str, Block], indent: int = 0) -> str:
    """Convert a single block to scratchblocks notation."""
    if block.opcode not in OPCODE_MAP:
        return f"{' ' * indent}// Unknown block: {block.opcode}"
    
    template = OPCODE_MAP[block.opcode]
    
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
    
    # Clean up any remaining placeholders
    import re
    result = re.sub(r'\{[A-Z_]+\}', '?', result)
    
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
