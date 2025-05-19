"""
Implementation of the up command.
"""

import os
import time
import yaml
import signal
import traceback
import sys
from typing import Dict, Any, List, Optional

from rich.table import Table

from tide.core.utils import launch_from_config
from tide.config import load_config, TideConfig
from tide.cli.utils import console
from tide.core.node import BaseNode

def cmd_up(args, *, run_duration: Optional[float] = None) -> int:
    """
    Run a Tide project.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    config_file = args.config
    
    # Check if config file exists
    if not os.path.exists(config_file):
        console.print(f"[bold red]Error:[/bold red] Configuration file '{config_file}' not found.")
        return 1
    
    # Load configuration
    try:
        config = load_config(config_file)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to load configuration: {e}")
        return 1
    
    # Show info about the configuration
    console.print("\n[bold]Configuration loaded:[/bold]")
    console.print(f"Session mode: [cyan]{config.session.mode}[/cyan]")
    
    node_table = Table(show_header=True, header_style="bold cyan")
    node_table.add_column("Node")
    node_table.add_column("Type")
    node_table.add_column("Robot ID")
    
    for i, node_config in enumerate(config.nodes):
        node_type = node_config.type
        robot_id = node_config.params.get('robot_id', '?')
        node_table.add_row(
            f"Node {i+1}",
            node_type,
            robot_id
        )
    
    console.print(node_table)
    console.print("\n[bold]Starting nodes...[/bold]")
    
    nodes = []  # Initialize nodes list
    shutdown_in_progress = False
    
    # Define signal handler with proper closure
    def shutdown_handler(sig=None, frame=None):
        nonlocal shutdown_in_progress
        
        # Prevent multiple calls to shutdown
        if shutdown_in_progress:
            return
            
        shutdown_in_progress = True
        console.print("\n[bold yellow]Shutting down...[/bold yellow]")
        
        # Stop all nodes
        for node in nodes:
            try:
                node.stop()
            except Exception as e:
                # Just log errors during shutdown
                pass
                
        console.print("[bold green]Nodes stopped.[/bold green]")
        sys.exit(0)
    
    try:
        # Launch nodes from config
        nodes = launch_from_config(config)
        
        console.print(f"[bold green]Started {len(nodes)} nodes.[/bold green]")
        console.print("[italic]Press Ctrl+C to exit.[/italic]")
        
        # Verify that each node has threads
        for node in nodes:
            if not node.threads or len(node.threads) == 0:
                console.print(f"[yellow]Warning:[/yellow] Node {node.__class__.__name__} has no threads.")
        
        # Set up signal handler for clean shutdown
        signal.signal(signal.SIGINT, shutdown_handler)
        
        start_time = time.time()

        # Keep the main thread alive
        while True:
            time.sleep(1)
            if run_duration is not None and (time.time() - start_time) >= run_duration:
                shutdown_handler()
                break
        
    except ModuleNotFoundError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]Module import error:[/yellow] This usually happens for one of these reasons:")
        console.print("1. The node module paths in your config don't match your project structure")
        console.print("2. Your current directory isn't in the Python path")
        console.print("3. You're missing a required dependency")
        console.print("\nCheck your config.yaml and ensure all module paths are correct.")
        console.print("Try running from your project's root directory.")
        return 1
        
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        # Add full traceback for better debugging
        console.print("\n[dim]Traceback:[/dim]")
        console.print(traceback.format_exc())
        return 1
    finally:
        # Ensure cleanup happens even on unexpected errors
        if not shutdown_in_progress:
            shutdown_handler()
    
    return 0 