"""Dynamic Skill Loader for TenderMind AI.

Parses markdown files in the skills/ directory to extract metadata configurations
from YAML frontmatter and instructions from the body content.
"""

import os
import re
from typing import Any, Dict


def parse_yaml_fallback(frontmatter_str: str) -> Dict[str, Any]:
    """Fallback parser for simple YAML frontmatter.
    
    Supports key-value pairs, simple list items, and indented keys (e.g. under parameters:).
    
    Args:
        frontmatter_str: Unprocessed frontmatter string content.
        
    Returns:
        Dict[str, Any]: Structured dictionary mapping metadata keys to values.
    """
    metadata: Dict[str, Any] = {}
    lines = frontmatter_str.split("\n")
    
    current_section = None
    list_key = None
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
            
        # Determine indentation level (leading spaces count)
        leading_spaces = len(line) - len(line.lstrip(' '))
        
        # Check if list element
        if stripped.startswith("-"):
            item_val = stripped[1:].strip().strip('"').strip("'")
            if list_key:
                if list_key not in metadata:
                    metadata[list_key] = []
                elif not isinstance(metadata[list_key], list):
                    metadata[list_key] = [metadata[list_key]]
                metadata[list_key].append(item_val)
            continue
            
        if ":" in stripped:
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            
            # Clean quotes and parse primitive types
            if val:
                val = val.strip('"').strip("'")
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                else:
                    try:
                        if "." in val:
                            val = float(val)
                        else:
                            val = int(val)
                    except ValueError:
                        pass
            
            # Sub-key identification based on indentation
            if leading_spaces > 0 and current_section:
                if current_section not in metadata:
                    metadata[current_section] = {}
                metadata[current_section][key] = val if val != "" else []
                if val == "":
                    list_key = f"{current_section}.{key}"
            else:
                if val == "":
                    metadata[key] = {}
                    current_section = key
                    list_key = key
                else:
                    metadata[key] = val
                    current_section = None
                    list_key = None
                    
    # Flatten nested key representations (e.g., parameters.temperature)
    keys_to_delete = []
    for k, v in list(metadata.items()):
        if "." in k:
            sec, sub = k.split(".", 1)
            if sec not in metadata:
                metadata[sec] = {}
            metadata[sec][sub] = v
            keys_to_delete.append(k)
            
    for k in keys_to_delete:
        del metadata[k]
        
    return metadata


def load_agent_skill(skill_name: str) -> Dict[str, Any]:
    """Loads and parses an agent skill markdown file.
    
    Reads skills/<skill_name>/SKILL.md, extracting parameters, name, description,
    and instructions dynamically to feed system instruction configurations.
    
    Args:
        skill_name: Folder name inside skills/ representing the target agent skill.
        
    Returns:
        Dict[str, Any]: Extracted metadata configuration and instruction body.
        
    Raises:
        FileNotFoundError: If the target SKILL.md does not exist.
    """
    # Locate project root directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    skill_path = os.path.join(base_dir, "skills", skill_name, "SKILL.md")
    
    if not os.path.exists(skill_path):
        raise FileNotFoundError(f"Skill file not found at {skill_path}")
        
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not frontmatter_match:
        return {
            "name": skill_name,
            "description": "",
            "tools": [],
            "parameters": {},
            "instructions": content.strip()
        }
        
    frontmatter_str = frontmatter_match.group(1)
    body_str = frontmatter_match.group(2)
    
    # Safely load YAML metadata utilizing standard package if installed, else fallback
    try:
        import yaml
        metadata = yaml.safe_load(frontmatter_str) or {}
    except ImportError:
        metadata = parse_yaml_fallback(frontmatter_str)
        
    return {
        "name": metadata.get("name", skill_name),
        "description": metadata.get("description", ""),
        "tools": metadata.get("tools", []),
        "parameters": metadata.get("parameters", {}),
        "instructions": body_str.strip()
    }
