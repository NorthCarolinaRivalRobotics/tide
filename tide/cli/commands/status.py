"""
Implementation of the status command.
"""

import time
from typing import Dict, Any, List

from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from tide.cli.utils import console, discover_nodes

def cmd_status(args) -> int:
    """
    Show status of running Tide nodes.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    # Show spinner while discovering nodes
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Discovering Tide nodes..."),
        console=console
    ) as progress:
        task = progress.add_task("", total=1)
        
        # Discover nodes
        nodes = discover_nodes(timeout=args.timeout)
        
        progress.update(task, completed=1)
    
    # Display discovered nodes
    if not nodes:
        console.print("[yellow]No Tide nodes discovered on the network.[/yellow]")
        console.print("Make sure your Tide project is running.")
        return 0
    
    # Display nodes in a table
    console.print(f"\n[bold green]Discovered {len(nodes)} nodes:[/bold green]")
    
    status_table = Table(show_header=True, header_style="bold cyan")
    status_table.add_column("Robot ID")
    status_table.add_column("Group")
    status_table.add_column("Topic")
    
    for node in nodes:
        status_table.add_row(
            node['robot_id'],
            node['group'],
            node['topic']
        )
    
    console.print(status_table)
    
    return 0 