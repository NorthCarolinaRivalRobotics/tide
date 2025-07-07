"""
Implementation of the init command.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn

from tide.cli.utils import console, read_template, render_template
from tide import __version__

def create_project_structure(project_dir: Path, context: Dict[str, Any]) -> None:
    """
    Create a new Tide project with the required structure.
    
    Args:
        project_dir: Project directory path
        context: Template context variables
    """
    # Create directory structure
    config_dir = project_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create minimal template files
    templates = {
        "nodes/ping_node.py": project_dir / "ping_node.py",
        "nodes/pong_node.py": project_dir / "pong_node.py",
        "main.py": project_dir / "main.py",
        "config/config.yaml": config_dir / "config.yaml",
        "README.md": project_dir / "README.md",
        "requirements.txt": project_dir / "requirements.txt",
    }
    
    # Render and write each template
    for template_path, output_path in templates.items():
        # Load template
        template_content = read_template(f"{template_path}.template")
        
        # Render template
        if template_path == "requirements.txt":
            # Special case for requirements.txt to use version
            rendered_content = render_template(template_content, {"version": __version__})
        else:
            rendered_content = render_template(template_content, context)
        
        # Write file
        with open(output_path, "w") as f:
            f.write(rendered_content)
        
        # Make executable if it's a Python file
        if output_path.suffix == ".py":
            os.chmod(output_path, 0o755)

def cmd_init(args) -> int:
    """
    Initialize a new Tide project.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    project_name = args.project_name
    robot_id = args.robot_id
    force = args.force
    
    # Create project directory
    project_dir = Path(project_name)
    
    if project_dir.exists() and not force:
        console.print(f"[bold red]Error:[/bold red] Project directory '{project_name}' already exists.")
        console.print("Use --force to overwrite.")
        return 1
    
    # Prepare template context
    context = {
        "project_name": project_name,
        "robot_id": robot_id,
    }
    
    # Show progress
    console.print("[bold blue]Creating project...[/bold blue]")
    
    try:
        # Debug info
        console.print(f"Debug: Project dir: {project_dir}")
        console.print(f"Debug: Context: {context}")
        
        # Create individual files instead of using the function that's causing issues
        # Create directory structure
        config_dir = project_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create ping_node.py file
        console.print("Debug: Creating ping_node.py")
        template_content = read_template("nodes/ping_node.py.template")
        rendered_content = render_template(template_content, context)
        with open(project_dir / "ping_node.py", "w") as f:
            f.write(rendered_content)
        os.chmod(project_dir / "ping_node.py", 0o755)
        
        # Create pong_node.py file
        console.print("Debug: Creating pong_node.py")
        template_content = read_template("nodes/pong_node.py.template")
        rendered_content = render_template(template_content, context)
        with open(project_dir / "pong_node.py", "w") as f:
            f.write(rendered_content)
        os.chmod(project_dir / "pong_node.py", 0o755)
        
        
        # Create config.yaml file
        console.print("Debug: Creating config.yaml")
        template_content = read_template("config/config.yaml.template")
        rendered_content = render_template(template_content, context)
        with open(config_dir / "config.yaml", "w") as f:
            f.write(rendered_content)
        
        # Create README.md file
        console.print("Debug: Creating README.md")
        template_content = read_template("README.md.template")
        rendered_content = render_template(template_content, context)
        with open(project_dir / "README.md", "w") as f:
            f.write(rendered_content)
        
        # Create requirements.txt file
        console.print("Debug: Creating requirements.txt")
        template_content = read_template("requirements.txt.template")
        rendered_content = render_template(template_content, {"version": __version__})
        with open(project_dir / "requirements.txt", "w") as f:
            f.write(rendered_content)
        
        # Show success message
        console.print("\n[bold green]Project created successfully![/bold green]")
        console.print(f"\nProject: [bold]{project_name}[/bold]")
        console.print(f"Robot ID: [bold]{robot_id}[/bold]")
        
        # Display run instructions
        console.print("\nTo run your project:")
        console.print(f"1. cd {project_name}")
        console.print("2. tide up")
        
        # Display example information
        console.print("\nYour project includes ping and pong nodes that demonstrate the publisher/subscriber pattern.")
        console.print("You can customize the nodes and configuration to suit your needs.")
        
        return 0
        
    except Exception as e:
        import traceback
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print(f"[red]Traceback:[/red] {traceback.format_exc()}")
        return 1
