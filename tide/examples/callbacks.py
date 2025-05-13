#!/usr/bin/env python3
"""
Callback-based example showing how to use tide's callback system.

This example demonstrates:
1. Using callbacks to handle messages
2. Setting up a node with minimal logic in the step method
3. Publishing data when callbacks are triggered
"""

import asyncio
import math
import sys
import time
from datetime import datetime

from tide.core.node import BaseNode
from tide.models import Twist2D, Pose2D, to_zenoh_value, from_zenoh_value


class CallbackRobotNode(BaseNode):
    """
    A robot node that primarily uses callbacks to handle messages.
    """
    ROBOT_ID = "frogbot"  # Robot's unique ID
    GROUP = "control"     # Group for this node's topics
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # Override robot ID from config if provided
        if config and "robot_id" in config:
            self.ROBOT_ID = config["robot_id"]
        
        # State variables
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        self.linear_vel = 0.0
        self.angular_vel = 0.0
        
        self.last_update = time.time()
        
        # Use register_callback to set up message handlers
        self.register_callback("cmd/twist", self._on_cmd_vel)
        
        # You can register multiple callbacks for the same topic
        self.register_callback("cmd/twist", self._log_cmd_vel)
        
        print(f"CallbackRobotNode started for robot {self.ROBOT_ID}")
    
    def _on_cmd_vel(self, data):
        """Primary handler for command velocity messages."""
        try:
            # Convert from Zenoh data to Twist2D
            cmd = from_zenoh_value(data, Twist2D)
            
            # Extract linear and angular velocity
            self.linear_vel = cmd.linear.x
            self.angular_vel = cmd.angular
            
            print(f"Control: linear={self.linear_vel}, angular={self.angular_vel}")
        except Exception as e:
            print(f"Error processing command: {e}")
    
    def _log_cmd_vel(self, data):
        """Secondary handler to log command messages."""
        try:
            cmd = from_zenoh_value(data, Twist2D)
            print(f"LOG: Received command with timestamp: {cmd.timestamp}")
        except Exception:
            pass
    
    def _update_pose(self, dt):
        """Update pose based on current velocities and time delta."""
        if abs(self.angular_vel) < 1e-6:
            # Straight line motion
            self.x += self.linear_vel * dt * math.cos(self.theta)
            self.y += self.linear_vel * dt * math.sin(self.theta)
        else:
            # Arc motion
            radius = self.linear_vel / self.angular_vel
            self.x += radius * (-math.sin(self.theta) + math.sin(self.theta + self.angular_vel * dt))
            self.y += radius * (math.cos(self.theta) - math.cos(self.theta + self.angular_vel * dt))
            self.theta += self.angular_vel * dt
            
            # Normalize theta to [-pi, pi]
            self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
    
    async def step(self):
        """
        Main processing loop - minimal since we're using callbacks.
        Just update pose and publish state.
        """
        # Calculate time since last update
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Update position
        self._update_pose(dt)
        
        # Create and publish pose message
        pose = Pose2D(
            x=self.x,
            y=self.y,
            theta=self.theta,
            timestamp=datetime.now()
        )
        
        # Publish pose
        await self.put("state/pose2d", to_zenoh_value(pose))


class CommandPublisherNode(BaseNode):
    """
    Node that publishes commands to the robot.
    Demonstrates how to send commands to a specific robot ID.
    """
    ROBOT_ID = "command_center"  # Unique ID for this command node
    GROUP = "teleop"             # Group for this node's topics
    
    hz = 2.0  # Update at 2 Hz
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # Target robot to control
        self.target_robot = config.get("target_robot", "frogbot") if config else "frogbot"
        
        # Command pattern
        self.commands = [
            {"linear": 0.2, "angular": 0.0},   # Forward
            {"linear": 0.0, "angular": 0.3},   # Turn left
            {"linear": -0.1, "angular": 0.0},  # Backward
            {"linear": 0.0, "angular": -0.3},  # Turn right
        ]
        self.cmd_index = 0
        
        print(f"CommandPublisherNode started, controlling {self.target_robot}")
    
    async def step(self):
        """Send periodic commands to the target robot."""
        # Get the next command in the sequence
        cmd = self.commands[self.cmd_index]
        self.cmd_index = (self.cmd_index + 1) % len(self.commands)
        
        # Create command velocity message
        cmd_vel = Twist2D(
            linear={"x": cmd["linear"], "y": 0.0},
            angular=cmd["angular"],
            timestamp=datetime.now()
        )
        
        # Send command directly to the target robot
        key = f"/{self.target_robot}/cmd/twist"
        await self.z.put(key, to_zenoh_value(cmd_vel))
        
        # Print current command
        print(f"Sending to {self.target_robot}: linear={cmd['linear']}, angular={cmd['angular']}")


class StateMonitorNode(BaseNode):
    """
    Monitor node that watches for state updates using callbacks.
    """
    ROBOT_ID = "monitor"     # Unique ID for this monitor
    GROUP = "visualization"  # Group for this node's topics
    
    hz = 1.0  # Only run step() at 1 Hz
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # Target robot to monitor
        self.target_robot = config.get("target_robot", "frogbot") if config else "frogbot"
        
        # Subscribe to robot's pose using register_callback
        key = f"/{self.target_robot}/state/pose2d"
        self.register_callback(key, self._on_pose_update)
        
        self.last_pose = None
        print(f"StateMonitorNode started, watching {self.target_robot}")
    
    def _on_pose_update(self, data):
        """Callback for pose updates."""
        try:
            pose = from_zenoh_value(data, Pose2D)
            self.last_pose = pose
            
            # Handle the update immediately in the callback
            x = pose.x
            y = pose.y
            theta_deg = math.degrees(pose.theta)
            print(f"CALLBACK - Robot position: x={x:.2f}, y={y:.2f}, theta={theta_deg:.1f}°")
        except Exception as e:
            print(f"Error processing pose: {e}")
    
    async def step(self):
        """
        Very minimal step function - most logic is in callbacks.
        This just provides a heartbeat to show the node is alive.
        """
        if self.last_pose:
            # This would be where you'd do periodic processing of the data
            # rather than responding immediately in the callback
            print(f"Monitor heartbeat - last update: {self.last_pose.timestamp}")
        else:
            print("Waiting for robot pose updates...")


async def main():
    """Run the example."""
    robot_id = "frogbot"
    
    print(f"Starting callback-based example with robot ID: {robot_id}")
    
    # Create the nodes
    robot = CallbackRobotNode(config={"robot_id": robot_id})
    commander = CommandPublisherNode(config={"target_robot": robot_id})
    monitor = StateMonitorNode(config={"target_robot": robot_id})
    
    # Start all nodes
    robot_task = robot.start()
    commander_task = commander.start()
    monitor_task = monitor.start()
    
    try:
        # Run until interrupted
        await asyncio.gather(robot_task, commander_task, monitor_task)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Cleanup
        await robot.stop()
        await commander.stop()
        await monitor.stop()
        print("Nodes stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(0) 