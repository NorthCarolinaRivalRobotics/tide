#!/usr/bin/env python3
"""
Example sensor node that publishes simulated data.
"""

import asyncio
import time
import random
import math
import sys
from datetime import datetime

from tide.core.node import BaseNode
from tide.models.common import LaserScan, Vector3
from tide.models.serialization import to_zenoh_value, from_zenoh_value


class SensorNode(BaseNode):
    """
    Node that publishes simulated sensor data.
    """
    ROBOT_ID = "robot1"  # Robot's unique ID
    GROUP = "sensor"     # Group for this node's topics
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # Configuration
        self.update_rate = 10.0  # Hz
        if config and "update_rate" in config:
            self.update_rate = config["update_rate"]
            
        # Override default update rate
        self.hz = self.update_rate
        
        # Simulation parameters
        self.obstacle_positions = [
            (3.0, 0.0),   # Obstacle at 3m directly ahead
            (-1.0, 2.0),  # Obstacle to the left
            (2.0, -2.5),  # Obstacle to the right
            (-2.0, -1.0), # Obstacle behind left
        ]
        
        print(f"SensorNode started for robot {self.ROBOT_ID}")
    
    def simulate_lidar(self, robot_x=0.0, robot_y=0.0, robot_theta=0.0):
        """
        Simulate a lidar scan based on robot position and obstacle positions.
        
        Args:
            robot_x: Robot X position
            robot_y: Robot Y position
            robot_theta: Robot heading (radians)
            
        Returns:
            LaserScan object
        """
        num_points = 100
        angle_min = -math.pi
        angle_max = math.pi
        angle_increment = (angle_max - angle_min) / num_points
        
        # Initialize ranges at max range
        max_range = 20.0
        ranges = [max_range] * num_points
        
        # For each obstacle, calculate distance from each scan angle
        for obs_x, obs_y in self.obstacle_positions:
            # Convert obstacle position to robot-relative coordinates
            rel_x = obs_x - robot_x
            rel_y = obs_y - robot_y
            
            # Rotate to robot's reference frame
            rot_x = rel_x * math.cos(-robot_theta) - rel_y * math.sin(-robot_theta)
            rot_y = rel_x * math.sin(-robot_theta) + rel_y * math.cos(-robot_theta)
            
            # Calculate distance and angle to obstacle
            distance = math.sqrt(rot_x**2 + rot_y**2)
            angle = math.atan2(rot_y, rot_x)
            
            # Find which laser beam this would hit
            beam_index = int((angle - angle_min) / angle_increment)
            if 0 <= beam_index < num_points:
                # Add some noise to the measurement
                noisy_distance = distance + random.uniform(-0.05, 0.05)
                # Update range if this obstacle is closer than current value
                if noisy_distance < ranges[beam_index]:
                    ranges[beam_index] = noisy_distance
        
        # Create and return the LaserScan message
        return LaserScan(
            angle_min=angle_min,
            angle_max=angle_max,
            angle_increment=angle_increment,
            range_min=0.1,
            range_max=max_range,
            ranges=ranges
        )
    
    def simulate_imu(self):
        """
        Simulate IMU data.
        
        Returns:
            Vector3 object for acceleration
        """
        # Simulate gravity + random noise
        return Vector3(
            x=random.uniform(-0.1, 0.1),
            y=random.uniform(-0.1, 0.1),
            z=9.81 + random.uniform(-0.05, 0.05)
        )
    
    async def step(self):
        """Publish simulated sensor data."""
        # Get robot pose to use for simulation
        # In a real scenario, we'd subscribe to the robot's pose
        # Here we just use a fixed position and simulate movement
        t = time.time()
        robot_x = 0.0
        robot_y = 0.0
        robot_theta = math.sin(0.1 * t)  # Robot slowly looking around
        
        # Simulate lidar data
        scan = self.simulate_lidar(robot_x, robot_y, robot_theta)
        
        # Publish scan data
        await self.put("lidar/scan", to_zenoh_value(scan))
        
        # Simulate and publish IMU data
        accel = self.simulate_imu()
        await self.put("imu/accel", to_zenoh_value(accel))
        

class SensorProcessorNode(BaseNode):
    """
    Node that processes sensor data.
    """
    ROBOT_ID = "robot1"
    GROUP = "processor"
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        
        # State variables
        self.last_scan = None
        self.last_scan_time = None
        self.last_accel = None
        self.last_accel_time = None
        
        # Subscribe to sensor data
        self.subscribe("sensor/lidar/scan", self._on_scan)
        self.subscribe("sensor/imu/accel", self._on_accel)
        
        print(f"SensorProcessorNode started for robot {self.ROBOT_ID}")
    
    def _on_scan(self, data):
        """Handle incoming laser scan data."""
        try:
            scan = from_zenoh_value(data, LaserScan)
            self.last_scan = scan
            self.last_scan_time = time.time()
            
            # Calculate minimum distance
            min_range = min(scan.ranges)
            min_angle_idx = scan.ranges.index(min_range)
            min_angle = scan.angle_min + min_angle_idx * scan.angle_increment
            min_angle_deg = math.degrees(min_angle)
            
            print(f"Closest obstacle: {min_range:.2f}m at {min_angle_deg:.1f}°")
            
            # Detect obstacles by segments
            self.detect_obstacles_by_region(scan)
            
        except Exception as e:
            print(f"Error processing scan: {e}")
    
    def detect_obstacles_by_region(self, scan):
        """
        Divide the scan into regions and detect obstacles.
        
        Args:
            scan: LaserScan object
        """
        # Define regions (front, right, back, left)
        region_names = ["Front", "Right", "Back", "Left"]
        region_size = len(scan.ranges) // len(region_names)
        
        for i, name in enumerate(region_names):
            start_idx = i * region_size
            end_idx = (i + 1) * region_size
            region_ranges = scan.ranges[start_idx:end_idx]
            
            # Calculate region statistics
            min_range = min(region_ranges)
            avg_range = sum(region_ranges) / len(region_ranges)
            
            # Check if obstacle is close
            if min_range < 1.0:
                print(f"WARNING: Obstacle in {name} region: {min_range:.2f}m")
    
    def _on_accel(self, data):
        """Handle incoming acceleration data."""
        try:
            accel = from_zenoh_value(data, Vector3)
            self.last_accel = accel
            self.last_accel_time = time.time()
            
            # Calculate magnitude (should be ~9.8 m/s² when stationary due to gravity)
            magnitude = (accel.x**2 + accel.y**2 + accel.z**2)**0.5
            
            # Check for unusual accelerations
            if abs(magnitude - 9.81) > 0.5:
                print(f"Unusual acceleration: {magnitude:.2f}m/s² (diff from gravity: {magnitude-9.81:.2f})")
            
        except Exception as e:
            print(f"Error processing acceleration: {e}")
    
    async def step(self):
        """Main processing loop."""
        # Check if data is being received
        now = time.time()
        
        if self.last_scan_time and now - self.last_scan_time > 1.0:
            print("Warning: No LIDAR data received recently")
            
        if self.last_accel_time and now - self.last_accel_time > 1.0:
            print("Warning: No IMU data received recently")


async def main():
    """Run the example."""
    robot_id = "testbot"  # You can change this to your preferred robot name
    
    print(f"Starting sensor node example with robot ID: {robot_id}")
    
    # Create the nodes with the same robot ID
    sensor = SensorNode(config={"robot_id": robot_id, "update_rate": 5.0})
    processor = SensorProcessorNode(config={"robot_id": robot_id})
    
    # Start all nodes
    sensor_task = sensor.start()
    processor_task = processor.start()
    
    try:
        # Run until interrupted
        await asyncio.gather(sensor_task, processor_task)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Cleanup
        await sensor.stop()
        await processor.stop()
        print("Nodes stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(0) 