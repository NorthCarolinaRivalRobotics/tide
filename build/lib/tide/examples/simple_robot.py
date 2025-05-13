#!/usr/bin/env python3
"""
Simple example showing how to use the tide framework.

This example demonstrates:
1. Creating a custom node
2. Subscribing to command messages
3. Publishing state messages
4. Using the opinionated namespacing
"""

import math
import sys
import time
import signal
from datetime import datetime

from tide.core.node import BaseNode
from tide.models.common import Twist2D, Pose2D
from tide.models.serialization import to_zenoh_value, from_zenoh_value


class SimpleRobotNode(BaseNode):
    """
    A simple robot node that receives velocity commands and publishes position.
    
    Implements a basic integration of velocity to position.
    """
    ROBOT_ID = "simbot"  # Robot's unique ID
    GROUP = "example"    # Group for this node's topics
    
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
        
        # Subscribe to command velocity
        # Using the cmd/twist namespace
        self.subscribe("cmd/twist", self._on_cmd_vel)
        
        print(f"SimpleRobotNode started for robot {self.ROBOT_ID}")
    
    def _on_cmd_vel(self, data):
        """Handle incoming command velocity messages."""
        try:
            # Convert from Zenoh data to Twist2D
            cmd = from_zenoh_value(data, Twist2D)
            
            # Extract linear and angular velocity
            self.linear_vel = cmd.linear.x
            self.angular_vel = cmd.angular
            
            print(f"Received command: linear={self.linear_vel}, angular={self.angular_vel}")
        except Exception as e:
            print(f"Error processing command: {e}")
    
    def _update_pose(self, dt):
        """
        Update pose based on current velocities and time delta.
        
        Args:
            dt: Time delta in seconds
        """
        # Basic motion model with velocity integration
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
    
    def step(self):
        """Main processing loop for position updates and publishing."""
        # Calculate time since last update
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Update position
        self._update_pose(dt)
        
        # Create and publish pose message
        # Using the state/pose2d namespace
        pose = Pose2D(
            x=self.x,
            y=self.y,
            theta=self.theta,
            timestamp=datetime.now()
        )
        
        # Publish pose
        self.put("state/pose2d", to_zenoh_value(pose))


class TeleopNode(BaseNode):
    """
    Simple teleop node that sends periodic velocity commands.
    """
    ROBOT_ID = "simbot"  # Must match the robot to control
    GROUP = "teleop"     # Group for teleop-related topics
    
    hz = 10.0  # Update at 10 Hz
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # Override robot ID from config if provided
        if config and "robot_id" in config:
            self.ROBOT_ID = config["robot_id"]
            
        self.time_started = datetime.now()
        print(f"Teleop started, controlling {self.ROBOT_ID}")
    
    def step(self):
        """Send periodic velocity commands in a simple pattern."""
        # Calculate time since start
        now = datetime.now()
        elapsed = (now - self.time_started).total_seconds()
        
        # Create a simple pattern:
        # 0-5s: Forward
        # 5-10s: Turn left
        # 10-15s: Backward
        # 15-20s: Turn right
        # Repeat
        cycle = int(elapsed / 5) % 4
        
        lin_x = 0.0
        ang_z = 0.0
        
        if cycle == 0:
            lin_x = 0.2  # Forward
        elif cycle == 1:
            ang_z = 0.5  # Turn left
        elif cycle == 2:
            lin_x = -0.2  # Backward
        elif cycle == 3:
            ang_z = -0.5  # Turn right
            
        # Create command velocity message
        cmd_vel = Twist2D(
            linear={"x": lin_x, "y": 0.0},
            angular=ang_z,
            timestamp=datetime.now()
        )
        
        # Send command to the robot
        # We bypass the group here to put directly to the robot's command topic
        key = f"/{self.ROBOT_ID}/cmd/twist"
        self.put(key, to_zenoh_value(cmd_vel))
        
        # Print current command
        print(f"Sending: linear.x={lin_x}, angular={ang_z}")


class MonitorNode(BaseNode):
    """
    Monitor node that displays the robot's pose.
    """
    ROBOT_ID = "simbot"  # Must match the robot to monitor
    GROUP = "monitor"    # Group for monitoring-related topics
    
    hz = 1.0  # Update at 1 Hz
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # Override robot ID from config if provided
        if config and "robot_id" in config:
            self.ROBOT_ID = config["robot_id"]
            
        # Subscribe to robot's pose
        key = f"/{self.ROBOT_ID}/state/pose2d"
        self.subscribe(key, self._on_pose)
        
        self.last_pose = None
        print(f"Monitor started, watching {self.ROBOT_ID}")
    
    def _on_pose(self, data):
        """Handle incoming pose messages."""
        try:
            pose = from_zenoh_value(data, Pose2D)
            self.last_pose = pose
        except Exception as e:
            print(f"Error processing pose: {e}")
    
    def step(self):
        """Display robot state."""
        if self.last_pose:
            x = self.last_pose.x
            y = self.last_pose.y
            theta_deg = math.degrees(self.last_pose.theta)
            print(f"Robot at x={x:.2f}, y={y:.2f}, theta={theta_deg:.1f}°")
        else:
            print("Waiting for robot pose updates...")


def main():
    """Run the example."""
    robot_id = "frogbot"  # You can change this to your preferred robot name
    
    print(f"Starting simple tide example with robot ID: {robot_id}")
    
    # Create the nodes with the same robot ID
    simple_robot = SimpleRobotNode(config={"robot_id": robot_id})
    teleop = TeleopNode(config={"robot_id": robot_id})
    monitor = MonitorNode(config={"robot_id": robot_id})
    
    # Start all nodes
    simple_robot.start()
    teleop.start()
    monitor.start()
    
    # Set up signal handler for clean shutdown
    def signal_handler(sig, frame):
        print("\nShutting down...")
        # Cleanup
        simple_robot.stop()
        teleop.stop()
        monitor.stop()
        print("Nodes stopped")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        # Cleanup
        simple_robot.stop()
        teleop.stop()
        monitor.stop()
        print("Nodes stopped")


if __name__ == "__main__":
    main() 