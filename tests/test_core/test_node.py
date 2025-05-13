import time
import pytest
from tide.core.node import BaseNode

class MockNode(BaseNode):
    """Simple mock node implementation for testing BaseNode functionality."""
    GROUP = "test"
    
    def __init__(self, config=None):
        super().__init__(config=config)
        self.step_count = 0
    
    def step(self):
        """Increment step counter each time step is called."""
        self.step_count += 1


class TestBaseNode:
    """Test cases for the BaseNode class."""
    
    def test_initialization(self):
        """Test that a node can be initialized with proper config."""
        config = {"robot_id": "test_robot"}
        node = MockNode(config=config)
        
        assert node.ROBOT_ID == "test_robot"
        assert node.GROUP == "test"
        assert node.hz == 50.0  # Default value
    
    def test_key_generation(self):
        """Test that keys are properly generated."""
        node = MockNode(config={"robot_id": "test_robot"})
        
        # Test normal key
        key = "data"
        full_key = node._make_key(key)
        assert full_key == "test_robot/test/data"
        
        # Test absolute key
        abs_key = "/global/topic"
        full_abs_key = node._make_key(abs_key)
        assert full_abs_key == "global/topic"
    
    def test_start_stop(self):
        """Test that a node can be started and stopped."""
        node = MockNode()
        
        thread = node.start()
        assert thread.is_alive()
        
        # Wait a short time to allow some steps to occur
        time.sleep(0.1)
        
        # Stop the node
        node.stop()
        
        # Wait for the thread to stop
        thread.join(timeout=1.0)
        assert not thread.is_alive()
        
        # Verify steps occurred
        assert node.step_count > 0
    
    def test_pub_sub(self):
        """Test that nodes can publish and subscribe to topics."""
        # In this test, we'll have one node publish and another node subscribe
        node_pub = MockNode(config={"robot_id": "robot1"})
        node_sub = MockNode(config={"robot_id": "robot2"})
        
        # Create a simple flag to verify we received data
        received = False
        
        def callback(sample):
            nonlocal received
            received = True
        
        # Both nodes subscribe to the same topic but with different robot IDs
        # This creates cross-robot communication
        node_sub.subscribe("/shared/topic", callback)
        
        # Small delay to ensure subscription is registered
        time.sleep(0.2)
        
        # Publish to the shared topic
        node_pub.put("/shared/topic", "test_message")
        
        # Give some time for the message to be received
        time.sleep(0.3)
        
        # Clean up
        node_pub.stop()
        node_sub.stop()
        
        # Check if we received a message
        assert received, "No message was received"

    def test_get_take(self):
        """Test getting and taking values."""
        node = MockNode()
        
        # Subscribe first to ensure we have something to capture
        received_data = []
        def callback(sample):
            # Extract payload data from Zenoh Sample object
            received_data.append(sample)
        
        node.subscribe("test_topic", callback)
        
        # Put a value
        test_value = "test_value"
        node.put("test_topic", test_value)
        
        # Give some time for the message to be received
        time.sleep(0.1)
        
        # Check we received data through subscription
        assert len(received_data) > 0
        
        # At this point, our BaseNode's _latest_values should have the Zenoh sample
        # Test take which consumes the value
        taken_value = node.take("test_topic")
        assert taken_value is not None
        assert hasattr(taken_value, 'payload')
        
        # Take again should now be None
        empty_value = node.take("test_topic")
        assert empty_value is None
        
        # Clean up
        node.stop() 