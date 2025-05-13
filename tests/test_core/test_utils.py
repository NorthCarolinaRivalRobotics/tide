"""
Tests for the utility functions in the core module.
"""
import asyncio
import math
import pytest
from unittest.mock import patch, MagicMock

from tide.core.utils import (
    import_class,
    create_node,
    launch_from_config,
    quaternion_from_euler,
    euler_from_quaternion
)
from tide.core.node import BaseNode


class TestUtils:
    """Tests for utility functions."""
    
    @patch('importlib.import_module')
    def test_import_class(self, mock_import):
        """Test importing a class from a string path."""
        # Setup mock
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_module.TestClass = mock_class
        mock_import.return_value = mock_module
        
        # Call the function
        result = import_class("core.node.TestClass")
        
        # Check results
        mock_import.assert_called_once_with("tide.core.node")
        assert result == mock_class
    
    @pytest.mark.asyncio
    @patch('tide.core.utils.import_class')
    async def test_create_node(self, mock_import_class):
        """Test creating a node from a type string."""
        # Setup mock
        mock_node_class = MagicMock()
        mock_node = MagicMock()
        mock_node_class.return_value = mock_node
        mock_import_class.return_value = mock_node_class
        
        # Call the function
        params = {"param1": "value1", "param2": 123}
        result = await create_node("test.TestNode", params)
        
        # Check results
        mock_import_class.assert_called_once_with("test.TestNode")
        mock_node_class.assert_called_once_with(config=params)
        assert result == mock_node
    
    @pytest.mark.asyncio
    @patch('tide.core.utils.create_node')
    async def test_launch_from_config(self, mock_create_node, sample_config):
        """Test launching nodes from a configuration."""
        # Setup mock
        mock_node = MagicMock(spec=BaseNode)
        mock_node.start.return_value = MagicMock()
        mock_create_node.return_value = mock_node
        
        # Call the function
        result = await launch_from_config(sample_config)
        
        # Check results
        mock_create_node.assert_called_once_with(
            "test_module.TestNode",
            {"robot_id": "test_robot", "param1": "value1", "param2": 123}
        )
        mock_node.start.assert_called_once()
        assert len(result) == 1
        assert result[0] == mock_node
    
    def test_quaternion_from_euler(self):
        """Test converting Euler angles to quaternion."""
        # Test identity (0, 0, 0)
        q = quaternion_from_euler(0, 0, 0)
        assert math.isclose(q["w"], 1.0)
        assert math.isclose(q["x"], 0.0)
        assert math.isclose(q["y"], 0.0)
        assert math.isclose(q["z"], 0.0)
        
        # Test common rotations and check results
        # 90 degrees around X
        q = quaternion_from_euler(math.pi/2, 0, 0)
        assert math.isclose(q["w"], math.cos(math.pi/4))
        assert math.isclose(q["x"], math.sin(math.pi/4))
        assert math.isclose(q["y"], 0.0)
        assert math.isclose(q["z"], 0.0)
        
        # 90 degrees around Y
        q = quaternion_from_euler(0, math.pi/2, 0)
        assert math.isclose(q["w"], math.cos(math.pi/4))
        assert math.isclose(q["x"], 0.0)
        assert math.isclose(q["y"], math.sin(math.pi/4))
        assert math.isclose(q["z"], 0.0)
        
        # 90 degrees around Z
        q = quaternion_from_euler(0, 0, math.pi/2)
        assert math.isclose(q["w"], math.cos(math.pi/4))
        assert math.isclose(q["x"], 0.0)
        assert math.isclose(q["y"], 0.0)
        assert math.isclose(q["z"], math.sin(math.pi/4))
    
    def test_euler_from_quaternion(self):
        """Test converting quaternion to Euler angles."""
        # Test identity quaternion (1, 0, 0, 0)
        roll, pitch, yaw = euler_from_quaternion({"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0})
        assert math.isclose(roll, 0.0)
        assert math.isclose(pitch, 0.0)
        assert math.isclose(yaw, 0.0)
        
        # Test common rotations
        # 90 degrees around X
        q = {"w": math.cos(math.pi/4), "x": math.sin(math.pi/4), "y": 0.0, "z": 0.0}
        roll, pitch, yaw = euler_from_quaternion(q)
        assert math.isclose(roll, math.pi/2)
        assert math.isclose(pitch, 0.0)
        assert math.isclose(yaw, 0.0)
        
        # 90 degrees around Y
        q = {"w": math.cos(math.pi/4), "x": 0.0, "y": math.sin(math.pi/4), "z": 0.0}
        roll, pitch, yaw = euler_from_quaternion(q)
        assert math.isclose(roll, 0.0)
        assert math.isclose(pitch, math.pi/2)
        assert math.isclose(yaw, 0.0)
        
        # 90 degrees around Z
        q = {"w": math.cos(math.pi/4), "x": 0.0, "y": 0.0, "z": math.sin(math.pi/4)}
        roll, pitch, yaw = euler_from_quaternion(q)
        assert math.isclose(roll, 0.0)
        assert math.isclose(pitch, 0.0)
        assert math.isclose(yaw, math.pi/2)
    
    def test_euler_quaternion_conversion_roundtrip(self):
        """Test the roundtrip conversion from Euler to quaternion and back."""
        # Test a set of angles
        test_angles = [
            (0, 0, 0),  # Identity
            (math.pi/4, 0, 0),  # 45 degrees X
            (0, math.pi/3, 0),  # 60 degrees Y
            (0, 0, math.pi/2),  # 90 degrees Z
            (math.pi/6, math.pi/4, math.pi/3),  # Arbitrary rotation
        ]
        
        for original_roll, original_pitch, original_yaw in test_angles:
            # Convert to quaternion
            q = quaternion_from_euler(original_roll, original_pitch, original_yaw)
            
            # Convert back to Euler
            roll, pitch, yaw = euler_from_quaternion(q)
            
            # Check that we recover the original angles
            # Note: Due to singularities and different representations
            # of the same rotation, we may not always get identical values.
            # Testing with some tolerance.
            assert math.isclose(roll, original_roll, abs_tol=1e-6) or \
                   math.isclose(roll % (2 * math.pi), original_roll % (2 * math.pi), abs_tol=1e-6)
            assert math.isclose(pitch, original_pitch, abs_tol=1e-6) or \
                   math.isclose(pitch % (2 * math.pi), original_pitch % (2 * math.pi), abs_tol=1e-6)
            assert math.isclose(yaw, original_yaw, abs_tol=1e-6) or \
                   math.isclose(yaw % (2 * math.pi), original_yaw % (2 * math.pi), abs_tol=1e-6) 