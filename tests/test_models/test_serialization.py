"""
Tests for the serialization utilities using property-based testing.
"""
import json
import pytest
from datetime import datetime
from hypothesis import given, assume, strategies as st

from tide.models.serialization import (
    to_json,
    to_dict,
    to_zenoh_value,
    from_zenoh_value
)
from tide.models.common import (
    Twist2D,
    Pose2D,
    Vector2,
    TideMessage
)


# Define strategies for different types of models
@st.composite
def vector2_strategy(draw):
    """Strategy to generate Vector2 instances."""
    x = draw(st.floats(min_value=-1000, max_value=1000))
    y = draw(st.floats(min_value=-1000, max_value=1000))
    return Vector2(x=x, y=y)


@st.composite
def pose2d_strategy(draw):
    """Strategy to generate Pose2D instances."""
    x = draw(st.floats(min_value=-1000, max_value=1000))
    y = draw(st.floats(min_value=-1000, max_value=1000))
    theta = draw(st.floats(min_value=-6.28, max_value=6.28))
    return Pose2D(x=x, y=y, theta=theta)


@st.composite
def twist2d_strategy(draw):
    """Strategy to generate Twist2D instances."""
    linear = draw(vector2_strategy())
    angular = draw(st.floats(min_value=-10.0, max_value=10.0))
    return Twist2D(linear=linear, angular=angular)


class TestSerialization:
    """Tests for serialization functions."""
    
    def test_to_json_basic(self):
        """Test basic to_json functionality."""
        msg = Pose2D(x=1.0, y=2.0, theta=3.0)
        json_str = to_json(msg)
        
        # Parse and verify JSON
        data = json.loads(json_str)
        assert data["x"] == 1.0
        assert data["y"] == 2.0
        assert data["theta"] == 3.0
        assert "timestamp" in data
    
    def test_to_dict_basic(self):
        """Test basic to_dict functionality."""
        msg = Pose2D(x=1.0, y=2.0, theta=3.0)
        data = to_dict(msg)
        
        assert data["x"] == 1.0
        assert data["y"] == 2.0
        assert data["theta"] == 3.0
        assert "timestamp" in data
    
    def test_to_zenoh_value_basic(self):
        """Test basic to_zenoh_value functionality."""
        msg = Pose2D(x=1.0, y=2.0, theta=3.0)
        value = to_zenoh_value(msg)
        
        assert isinstance(value, bytes)
        
        # Parse and verify
        data = json.loads(value.decode('utf-8'))
        assert data["x"] == 1.0
        assert data["y"] == 2.0
        assert data["theta"] == 3.0
        assert "timestamp" in data
    
    def test_from_zenoh_value_basic(self):
        """Test basic from_zenoh_value functionality."""
        # Create a message, convert to Zenoh value
        original = Pose2D(x=1.0, y=2.0, theta=3.0)
        value = to_zenoh_value(original)
        
        # Convert back
        reconstructed = from_zenoh_value(value, Pose2D)
        
        # Verify
        assert reconstructed.x == 1.0
        assert reconstructed.y == 2.0
        assert reconstructed.theta == 3.0
    
    @given(vec=vector2_strategy())
    def test_vector2_roundtrip(self, vec):
        """Test Vector2 serialization/deserialization roundtrip."""
        # Serialization
        zenoh_value = to_zenoh_value(vec)
        
        # Deserialization
        reconstructed = from_zenoh_value(zenoh_value, Vector2)
        
        # Check that the reconstructed object matches the original
        assert reconstructed.x == vec.x
        assert reconstructed.y == vec.y
    
    @given(pose=pose2d_strategy())
    def test_pose2d_roundtrip(self, pose):
        """Test Pose2D serialization/deserialization roundtrip."""
        # Serialization
        zenoh_value = to_zenoh_value(pose)
        
        # Deserialization
        reconstructed = from_zenoh_value(zenoh_value, Pose2D)
        
        # Check that the reconstructed object matches the original
        assert reconstructed.x == pose.x
        assert reconstructed.y == pose.y
        assert reconstructed.theta == pose.theta
    
    @given(twist=twist2d_strategy())
    def test_twist2d_roundtrip(self, twist):
        """Test Twist2D serialization/deserialization roundtrip."""
        # Serialization
        zenoh_value = to_zenoh_value(twist)
        
        # Deserialization
        reconstructed = from_zenoh_value(zenoh_value, Twist2D)
        
        # Check that the reconstructed object matches the original
        assert reconstructed.linear.x == twist.linear.x
        assert reconstructed.linear.y == twist.linear.y
        assert reconstructed.angular == twist.angular
    
    @given(
        model_type=st.sampled_from([Vector2, Pose2D, Twist2D]),
        data_format=st.sampled_from(['bytes', 'str', 'dict'])
    )
    def test_from_zenoh_value_formats(self, model_type, data_format):
        """Test that from_zenoh_value handles different data formats."""
        # Create a simple instance of the model
        if model_type == Vector2:
            model = Vector2(x=1.0, y=2.0)
        elif model_type == Pose2D:
            model = Pose2D(x=1.0, y=2.0, theta=3.0)
        elif model_type == Twist2D:
            model = Twist2D(linear=Vector2(x=1.0, y=0.0), angular=0.5)
        
        # Get data in the specified format
        if data_format == 'bytes':
            data = to_zenoh_value(model)
        elif data_format == 'str':
            data = to_json(model)
        elif data_format == 'dict':
            data = to_dict(model)
        
        # Try to reconstruct the model
        reconstructed = from_zenoh_value(data, model_type)
        
        # Verify it worked
        assert isinstance(reconstructed, model_type)
    
    @pytest.mark.parametrize("input_data", [
        b'{"invalid": true}',
        '{"invalid": true}',
        {"invalid": True}
    ])
    def test_from_zenoh_value_invalid_data(self, input_data):
        """Test from_zenoh_value with invalid data formats."""
        # This should not raise an exception but create an empty model
        result = from_zenoh_value(input_data, Vector2)
        assert isinstance(result, Vector2)
    
    @given(
        x=st.floats(min_value=-1000, max_value=1000),
        y=st.floats(min_value=-1000, max_value=1000)
    )
    def test_vector2_properties(self, x, y):
        """Property-based test for Vector2 serialization."""
        # Create a Vector2
        vec = Vector2(x=x, y=y)
        
        # Convert to dictionary
        data = to_dict(vec)
        
        # Verify properties
        assert data["x"] == vec.x
        assert data["y"] == vec.y
    
    @given(
        linear_x=st.floats(min_value=-10.0, max_value=10.0),
        linear_y=st.floats(min_value=-10.0, max_value=10.0),
        angular=st.floats(min_value=-5.0, max_value=5.0)
    )
    def test_twist2d_properties(self, linear_x, linear_y, angular):
        """Property-based test for Twist2D serialization."""
        # Create a Twist2D
        twist = Twist2D(
            linear=Vector2(x=linear_x, y=linear_y),
            angular=angular
        )
        
        # Convert to dictionary and verify properties
        data = to_dict(twist)
        assert data["linear"]["x"] == linear_x
        assert data["linear"]["y"] == linear_y
        assert data["angular"] == angular
        
        # The timestamp should be present
        assert "timestamp" in data 