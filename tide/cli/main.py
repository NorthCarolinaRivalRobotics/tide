"""
Main entry point for the Tide CLI.
"""

import sys
import argparse

from tide import __version__
from tide.cli.utils import print_banner
from tide.cli.commands import (
    cmd_init,
    cmd_up,
    cmd_status,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser used by the Tide CLI."""
    parser = argparse.ArgumentParser(
        description="Tide Robotics Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Tide {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    init_parser = subparsers.add_parser(
        "init", help="Initialize a new Tide project"
    )
    init_parser.add_argument("project_name", help="Name of the project to create")
    init_parser.add_argument(
        "--robot-id", default="myrobot", help="Default robot ID to use"
    )
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing project")


    up_parser = subparsers.add_parser("up", help="Run a Tide project")
    up_parser.add_argument(
        "--config", default="config/config.yaml", help="Path to configuration file"
    )

    status_parser = subparsers.add_parser(
        "status", help="Show status of running Tide nodes"
    )
    status_parser.add_argument(
        "--timeout", type=float, default=2.0, help="Discovery timeout in seconds"
    )

    return parser

def main(argv=None):
    """Entry point for the Tide CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Display banner
    print_banner()
    
    # No command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    try:
        if args.command == 'init':
            result = cmd_init(args)
            sys.exit(result)

        elif args.command == 'up':
            result = cmd_up(args)
            sys.exit(result)

        elif args.command == 'status':
            result = cmd_status(args)
            sys.exit(result)
            
    except Exception as e:
        from tide.cli.utils import console
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
