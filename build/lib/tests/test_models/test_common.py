"""
Tests for the common message models.
"""
import time
import pytest
from datetime import datetime, timedelta

from tide.models.common import (
    TideMessage,
    Vector2,
    Vector3,
    Quaternion,
    Header,
    Twist2D,
    Twist3D,
    Pose2D,
    Pose3D,
    Acceleration3D,
    OccupancyGrid2D,
    LaserScan,
    Image
)

class TestCommonModels:
    """Tests for common message models."""
    
    def test_tide_message(self):
        """Test the base TideMessage class."""
        # Test default timestamp
        before = datetime.now()
        time.sleep(0.001)  # Ensure timestamp is after 'before'
        msg = TideMessage()
        time.sleep(0.001)  # Ensure 'after' is after timestamp
        after = datetime.now()
        
        assert before < msg.timestamp < after
        
        # Test custom timestamp
        custom_time = datetime.now() - timedelta(days=1)
        msg = TideMessage(timestamp=custom_time)
        assert msg.timestamp == custom_time
    
    def test_vector2(self):
        """Test the Vector2 model."""
        # Test defaults
        v = Vector2()
        assert v.x == 0.0
        assert v.y == 0.0
        
        # Test custom values
        v = Vector2(x=1.5, y=-2.5)
        assert v.x == 1.5
        assert v.y == -2.5
    
    def test_vector3(self):
        """Test the Vector3 model."""
        # Test defaults
        v = Vector3()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0
        
        # Test custom values
        v = Vector3(x=1.5, y=-2.5, z=3.0)
        assert v.x == 1.5
        assert v.y == -2.5
        assert v.z == 3.0
    
    def test_quaternion(self):
        """Test the Quaternion model."""
        # Test defaults (identity quaternion)
        q = Quaternion()
        assert q.x == 0.0
        assert q.y == 0.0
        assert q.z == 0.0
        assert q.w == 1.0  # Identity quaternion
        
        # Test custom values
        q = Quaternion(x=0.5, y=0.5, z=0.5, w=0.5)
        assert q.x == 0.5
        assert q.y == 0.5
        assert q.z == 0.5
        assert q.w == 0.5
    
    def test_header(self):
        """Test the Header model."""
        # Test defaults
        h = Header()
        assert h.frame_id == ""
        assert isinstance(h.stamp, datetime)
        
        # Test custom values
        custom_time = datetime.now() - timedelta(hours=2)
        h = Header(frame_id="base_link", stamp=custom_time)
        assert h.frame_id == "base_link"
        assert h.stamp == custom_time
    
    def test_twist2d(self):
        """Test the Twist2D model."""
        # Test defaults
        t = Twist2D()
        assert t.linear.x == 0.0
        assert t.linear.y == 0.0
        assert t.angular == 0.0
        assert isinstance(t.timestamp, datetime)
        
        # Test custom values
        custom_time = datetime.now() - timedelta(minutes=5)
        t = Twist2D(
            linear=Vector2(x=1.0, y=0.5),
            angular=0.2,
            timestamp=custom_time
        )
        assert t.linear.x == 1.0
        assert t.linear.y == 0.5
        assert t.angular == 0.2
        assert t.timestamp == custom_time
        
        # Test with dictionary for linear
        t = Twist2D(linear={"x": 2.0, "y": -1.0}, angular=-0.3)
        assert t.linear.x == 2.0
        assert t.linear.y == -1.0
        assert t.angular == -0.3
    
    def test_twist3d(self):
        """Test the Twist3D model."""
        # Test defaults
        t = Twist3D()
        assert t.linear.x == 0.0
        assert t.linear.y == 0.0
        assert t.linear.z == 0.0
        assert t.angular.x == 0.0
        assert t.angular.y == 0.0
        assert t.angular.z == 0.0
        
        # Test custom values
        t = Twist3D(
            linear=Vector3(x=1.0, y=0.5, z=-0.2),
            angular=Vector3(x=0.1, y=0.2, z=0.3)
        )
        assert t.linear.x == 1.0
        assert t.linear.y == 0.5
        assert t.linear.z == -0.2
        assert t.angular.x == 0.1
        assert t.angular.y == 0.2
        assert t.angular.z == 0.3
    
    def test_pose2d(self):
        """Test the Pose2D model."""
        # Test defaults
        p = Pose2D()
        assert p.x == 0.0
        assert p.y == 0.0
        assert p.theta == 0.0
        
        # Test custom values
        p = Pose2D(x=1.0, y=2.0, theta=3.14)
        assert p.x == 1.0
        assert p.y == 2.0
        assert p.theta == 3.14
    
    def test_pose3d(self):
        """Test the Pose3D model."""
        # Test defaults
        p = Pose3D()
        assert p.position.x == 0.0
        assert p.position.y == 0.0
        assert p.position.z == 0.0
        assert p.orientation.x == 0.0
        assert p.orientation.y == 0.0
        assert p.orientation.z == 0.0
        assert p.orientation.w == 1.0
        
        # Test custom values
        p = Pose3D(
            position=Vector3(x=1.0, y=2.0, z=3.0),
            orientation=Quaternion(x=0.0, y=0.0, z=0.7071, w=0.7071)
        )
        assert p.position.x == 1.0
        assert p.position.y == 2.0
        assert p.position.z == 3.0
        assert p.orientation.x == 0.0
        assert p.orientation.y == 0.0
        assert p.orientation.z == 0.7071
        assert p.orientation.w == 0.7071
    
    def test_acceleration3d(self):
        """Test the Acceleration3D model."""
        # Test defaults
        a = Acceleration3D()
        assert a.linear.x == 0.0
        assert a.linear.y == 0.0
        assert a.linear.z == 0.0
        assert a.angular.x == 0.0
        assert a.angular.y == 0.0
        assert a.angular.z == 0.0
        
        # Test custom values
        a = Acceleration3D(
            linear=Vector3(x=1.0, y=2.0, z=3.0),
            angular=Vector3(x=0.1, y=0.2, z=0.3)
        )
        assert a.linear.x == 1.0
        assert a.linear.y == 2.0
        assert a.linear.z == 3.0
        assert a.angular.x == 0.1
        assert a.angular.y == 0.2
        assert a.angular.z == 0.3
    
    def test_laser_scan(self):
        """Test the LaserScan model."""
        # We can't test defaults because some fields are required
        scan = LaserScan(
            header=Header(frame_id="lidar"),
            angle_min=-1.57,
            angle_max=1.57,
            angle_increment=0.01,
            time_increment=0.0001,
            scan_time=0.1,
            range_min=0.1,
            range_max=10.0,
            ranges=[1.0, 2.0, 3.0],
            intensities=[100, 200, 300]
        )
        
        assert scan.header.frame_id == "lidar"
        assert scan.angle_min == -1.57
        assert scan.angle_max == 1.57
        assert scan.angle_increment == 0.01
        assert scan.time_increment == 0.0001
        assert scan.scan_time == 0.1
        assert scan.range_min == 0.1
        assert scan.range_max == 10.0
        assert scan.ranges == [1.0, 2.0, 3.0]
        assert scan.intensities == [100, 200, 300]
    
    def test_occupancy_grid(self):
        """Test the OccupancyGrid2D model."""
        grid = OccupancyGrid2D(
            header=Header(frame_id="map"),
            width=10,
            height=10,
            resolution=0.1,
            origin=Pose2D(x=0.0, y=0.0, theta=0.0),
            data=[0] * 100  # 10x10 empty grid
        )
        
        assert grid.header.frame_id == "map"
        assert grid.width == 10
        assert grid.height == 10
        assert grid.resolution == 0.1
        assert grid.origin.x == 0.0
        assert grid.origin.y == 0.0
        assert grid.origin.theta == 0.0
        assert len(grid.data) == 100
        assert all(val == 0 for val in grid.data)
    
    def test_image(self):
        """Test the Image model."""
        img = Image(
            header=Header(frame_id="camera"),
            height=480,
            width=640,
            encoding="rgb8",
            is_bigendian=False,
            step=1920,  # 640 * 3 (RGB)
            data=b'\x00' * (640 * 480 * 3)  # Black image
        )
        
        assert img.header.frame_id == "camera"
        assert img.height == 480
        assert img.width == 640
        assert img.encoding == "rgb8"
        assert img.is_bigendian == False
        assert img.step == 1920
        assert len(img.data) == 640 * 480 * 3 