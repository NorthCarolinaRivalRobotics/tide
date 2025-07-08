"""
Utility functions for the Tide CLI.
"""

import os
import sys
import logging
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import zenoh
from rich.console import Console
from rich.logging import RichHandler

from tide import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("tide.cli")

# Initialize console
console = Console()

def print_banner():
    """Display the Tide banner."""
    banner = r"""
  _______   _        _          
 |__   __| (_)      | |         
    | |     _    __| |   ___    
    | |    | |  / _` |  / _ \   
    | |    | | | (_| | |  __/   
    |_|    |_|  \__,_|  \___|   
    
    """
    console.print(f"[bold blue]{banner}[/bold blue]")
    console.print(f"[bold cyan]Tide Robotics Framework v{__version__}[/bold cyan]")
    console.print("A lightweight, strongly-typed framework based on Zenoh\n")

def read_template(template_path: Union[str, Path]) -> str:
    """
    Read a template file.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        The template content as a string
    """
    template_dir = Path(__file__).parent / "templates"
    full_path = template_dir / template_path
    
    try:
        with open(full_path, "r") as f:
            return f.read()
    except Exception as e:
        log.error(f"Error reading template {template_path}: {e}")
        raise

def render_template(template_content: str, context: Dict[str, Any]) -> str:
    """
    Render a template with the given context.
    
    Args:
        template_content: The template content
        context: Dictionary of template variables
        
    Returns:
        The rendered template
    """
    # Replace only placeholders that are marked for replacement
    # We escape curly braces in the template content to avoid replacing code
    result = template_content
    
    # Replace each key in the context
    for key, value in context.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(value))
    
    return result

def discover_nodes(timeout: float = 2.0) -> List[Dict[str, Any]]:
    """
    Discover Tide nodes on the network.
    
    Args:
        timeout: Time to wait for responses
        
    Returns:
        List of discovered nodes
    """
    # Create a zenoh session for discovery
    z = zenoh.open(zenoh.Config())

    # Query for nodes across all groups
    discovered_nodes = []
    
    # Wait for responses
    start_time = time.time()
    
    try:
        # Query for anything matching the robot_id/group/topic pattern
        # This allows discovery of nodes even if they don't publish to the
        # reserved "state" group.
        # Query with wildcard allowing any number of topic segments
        # This supports topics like "robot/group/sub/topic"
        replies = z.get("*/*/**")
        
        while time.time() - start_time < timeout:
            # Process any new replies
            for reply in replies:
                if hasattr(reply, 'ok'):
                    # KeyExpr objects in the Python zenoh bindings do not
                    # implement a `to_string()` method. Casting to `str` works
                    # across versions, so use that to retrieve the key text.
                    key_parts = str(reply.ok.key_expr).split('/')
                    if len(key_parts) >= 3:
                        # key_parts contains [robot_id, group, ...]
                        robot_id = key_parts[0]
                        group = key_parts[1]
                        topic = '/'.join(key_parts[2:])
                        
                        # Add to discovered nodes if not already present
                        node_entry = {
                            'robot_id': robot_id,
                            'group': group,
                            'topic': topic,
                            'timestamp': time.time()
                        }
                        
                        # Check if this robot_id is already in our list
                        found = False
                        for existing in discovered_nodes:
                            if existing['robot_id'] == robot_id and existing['group'] == group:
                                found = True
                                break
                                
                        if not found:
                            discovered_nodes.append(node_entry)
            
            # Sleep briefly to avoid spinning
            time.sleep(0.1)
    
    except Exception as e:
        log.error(f"Error during node discovery: {e}")
    
    finally:
        z.close()
    
    return discovered_nodes 