"""
Implementation of the init-pingpong command.
"""

import os
from pathlib import Path

from tide.cli.utils import console, read_template, render_template
from tide.cli.commands.init import create_config_only

def cmd_init_pingpong(args) -> int:
    """
    Create ping and pong node examples.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    robot_id = args.robot_id
    force = args.force
    
    # Determine where to put the nodes
    if hasattr(args, 'output_dir') and args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Default to using the project_name as the output directory if available,
        # otherwise use current directory
        if hasattr(args, 'project_name') and args.project_name:
            output_dir = Path(args.project_name)
        else:
            output_dir = Path(".")
    
    # Make sure the directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Paths for the two node files
    ping_path = output_dir / "ping_node.py"
    pong_path = output_dir / "pong_node.py"
    
    # Check if files exist already
    if os.path.exists(ping_path) and not force:
        console.print(f"[yellow]Warning:[/yellow] ping_node.py already exists, skipping.")
        ping_created = False
    else:
        ping_created = True
        
    if os.path.exists(pong_path) and not force:
        console.print(f"[yellow]Warning:[/yellow] pong_node.py already exists, skipping.")
        pong_created = False
    else:
        pong_created = True
    
    # If both files already exist and we're not forcing overwrite, abort
    if not ping_created and not pong_created:
        console.print("[yellow]Both files already exist. Use --force to overwrite.[/yellow]")
        return 1
    
    # Create config file if requested
    if hasattr(args, 'create_config') and args.create_config:
        config_path = output_dir / "config" / "pingpong_config.yaml"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Check if config exists
        if os.path.exists(config_path) and not force:
            console.print(f"[yellow]Warning:[/yellow] {config_path} already exists, skipping.")
        else:
            # Create a simple config with both nodes
            config_content = f"""# Ping-Pong example configuration
version: 1

robots:
  {robot_id}:
    nodes:
      # Ping node (publisher example)
      ping:
        class: ping_node.PingNode
        config:
          update_rate: 1.0  # Hz
      
      # Pong node (subscriber example)
      pong:
        class: pong_node.PongNode
        config:
          response_delay: 0.2  # seconds
"""
            try:
                with open(config_path, "w") as f:
                    f.write(config_content)
                console.print(f"[bold green]Config created at:[/bold green] {config_path}")
            except Exception as e:
                console.print(f"[bold red]Error creating config file:[/bold red] {e}")
    
    # Create the node files
    context = {
        "robot_id": robot_id
    }
    
    # Create ping node
    if ping_created:
        try:
            ping_template = read_template("nodes/ping_node.py.template")
            rendered_ping = render_template(ping_template, context)
            
            with open(ping_path, "w") as f:
                f.write(rendered_ping)
            
            # Make it executable
            os.chmod(ping_path, 0o755)
            
            console.print(f"[bold green]Ping node created at:[/bold green] {ping_path}")
        except Exception as e:
            console.print(f"[bold red]Error creating ping node:[/bold red] {e}")
            return 1
    
    # Create pong node
    if pong_created:
        try:
            pong_template = read_template("nodes/pong_node.py.template")
            rendered_pong = render_template(pong_template, context)
            
            with open(pong_path, "w") as f:
                f.write(rendered_pong)
            
            # Make it executable
            os.chmod(pong_path, 0o755)
            
            console.print(f"[bold green]Pong node created at:[/bold green] {pong_path}")
        except Exception as e:
            console.print(f"[bold red]Error creating pong node:[/bold red] {e}")
            return 1
    
    # Print instructions
    console.print("\n[bold green]Ping-Pong example created successfully![/bold green]")
    if hasattr(args, 'create_config') and args.create_config:
        console.print("\nYou can run your ping-pong example with:")
        console.print(f"[cyan]   tide up --config {config_path.relative_to(Path.cwd())}[/cyan]")
    else:
        console.print("\nTo run the nodes manually:")
        console.print(f"[cyan]   # Run these in separate terminals:[/cyan]")
        console.print(f"[cyan]   python {ping_path.relative_to(Path.cwd())}[/cyan]")
        console.print(f"[cyan]   python {pong_path.relative_to(Path.cwd())}[/cyan]")
    
    return 0 