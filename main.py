#!/usr/bin/env python3
"""
Entry point for the tide robot framework.
"""

import argparse
import sys
import yaml
import time
import signal

from tide.core.utils import launch_from_config
from tide.config import load_config


def main():
    """
    Launch nodes from a configuration file.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Tide framework launcher')
    parser.add_argument('config_file', help='Path to configuration file (YAML)')
    parser.add_argument('--dry-run', action='store_true', help='Check configuration without running nodes')
    args = parser.parse_args()
    
    print(f"Loading configuration from {args.config_file}")
    
    try:
        # Load configuration
        config = load_config(args.config_file)
            
        if args.dry_run:
            print("Dry run - checking configuration...")
            print(f"Session mode: {config.session.mode}")
            for i, node_cfg in enumerate(config.nodes):
                print(f"Node {i+1}: {node_cfg.type} - {node_cfg.params}")
            print("Configuration looks valid!")
            return 0
            
        # Launch nodes from config
        nodes = launch_from_config(config)
        
        print(f"Started {len(nodes)} nodes. Press Ctrl+C to exit.")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("Interrupted by user")
            # Stop all nodes
            for node in nodes:
                node.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
