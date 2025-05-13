"""
Implementation of the init-config command.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from tide.cli.utils import console, read_template, render_template
from tide.cli.commands.init import create_config_only

def cmd_init_config(args) -> int:
    """
    Create a default config.yaml file.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    output_path = args.output
    robot_id = args.robot_id
    force = args.force
    include_node = args.include_node
    
    # Create the config file using the shared function
    result = create_config_only(output_path, robot_id, force)
    if result != 0:
        return result
    
    # Create ping-pong nodes if requested
    if include_node:
        # Determine node path - place alongside config in the same directory or use config dir parent
        output_file = Path(output_path)
        node_dir = output_file.parent
        if node_dir.name.lower() in ["config", "configs", "configuration"]:
            node_dir = node_dir.parent
            
        ping_path = node_dir / "ping_node.py"
        pong_path = node_dir / "pong_node.py"
        
        # Prepare template context
        context = {
            "robot_id": robot_id
        }
        
        # Check if ping node exists
        if os.path.exists(ping_path) and not force:
            console.print(f"[yellow]Note:[/yellow] ping_node.py already exists, skipping.")
        else:
            try:
                # Load and render the ping template
                ping_template = read_template("nodes/ping_node.py.template")
                rendered_ping = render_template(ping_template, context)
                
                # Write the ping file
                with open(ping_path, "w") as f:
                    f.write(rendered_ping)
                
                # Make it executable
                os.chmod(ping_path, 0o755)
                
                console.print(f"[bold green]Ping node created at:[/bold green] {ping_path}")
            except Exception as e:
                console.print(f"[bold red]Error creating ping node file:[/bold red] {e}")
                return 1
        
        # Check if pong node exists
        if os.path.exists(pong_path) and not force:
            console.print(f"[yellow]Note:[/yellow] pong_node.py already exists, skipping.")
        else:
            try:
                # Load and render the pong template
                pong_template = read_template("nodes/pong_node.py.template")
                rendered_pong = render_template(pong_template, context)
                
                # Write the pong file
                with open(pong_path, "w") as f:
                    f.write(rendered_pong)
                
                # Make it executable
                os.chmod(pong_path, 0o755)
                
                console.print(f"[bold green]Pong node created at:[/bold green] {pong_path}")
            except Exception as e:
                console.print(f"[bold red]Error creating pong node file:[/bold red] {e}")
                return 1
                
        console.print("[green]You can run your project with:[/green] tide up")
    else:
        # Add a helpful note about the node paths
        console.print("\n[yellow]Note:[/yellow] To complete your project, you need to create node implementations.")
        console.print(f"You can create ping-pong example nodes with: tide init-config --include-node")
    
    return 0 