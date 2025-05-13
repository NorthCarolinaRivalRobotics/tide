"""
Tests for the BaseNode class and its functionality.
"""
import pytest
import time
import threading
from unittest.mock import MagicMock, patch

from tests.test_core.mock_node import MockBaseNode
from tide.models import Twist2D, to_zenoh_value


class TestNode(MockBaseNode):
    """Simple test node implementation."""
    ROBOT_ID = "testbot"
    GROUP = "test"
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        self.step_called = False
        self.callback_called = False
        self.callback_data = None
    
    def step(self):
        self.step_called = True
    
    def test_callback(self, data):
        self.callback_called = True
        self.callback_data = data


class TestBaseNode:
    """Tests for the BaseNode class."""
    
    def test_init(self):
        """Test node initialization."""
        node = TestNode()
        assert node.ROBOT_ID == "testbot"
        assert node.GROUP == "test"
        assert not node.step_called
        
        # Test config override
        node = TestNode(config={"robot_id": "custom"})
        assert node.ROBOT_ID == "custom"
    
    def test_make_key(self):
        """Test key creation with different patterns."""
        node = TestNode()
        
        # Test with GROUP
        assert node._make_key("topic") == "testbot/test/topic"
        
        # Test with absolute path
        assert node._make_key("/absolute/path") == "absolute/path"
        
        # Test without GROUP
        node.GROUP = ""
        assert node._make_key("topic") == "testbot/topic"
    
    def test_register_callback(self):
        """Test callback registration and invocation."""
        node = TestNode()
        
        try:
            # Register callback
            node.register_callback("data", node.test_callback)
            
            # Check callback is registered
            key = "testbot/test/data"
            assert key in node._callbacks
            assert node.test_callback in node._callbacks[key]
            
            # Simulate receiving data (directly publish to trigger callbacks)
            mock_data = {"value": 42}
            node.session.put(key, mock_data)
            
            # Small delay to ensure callback is processed
            time.sleep(0.01)
            
            # Check callback was called with data
            assert node.callback_called
            assert node.callback_data == mock_data
        finally:
            node.stop()
    
    def test_start_stop(self):
        """Test starting and stopping a node."""
        node = TestNode()
        
        try:
            # Start the node
            thread = node.start()
            assert len(node.threads) == 1
            assert thread in node.threads
            
            # Let it run briefly
            time.sleep(0.01)
            
            # Check that step was called
            assert node.step_called
        finally:
            # Stop the node
            node.stop()
            assert not node._running
            
            # Give it time to complete stopping
            time.sleep(0.01)
            
            # Check thread status
            for thread in node.threads:
                assert not thread.is_alive()
    
    def test_put_get(self):
        """Test putting and getting data."""
        node = TestNode()
        
        try:
            # Test data
            test_key = "data"
            test_data = "test_data"
            full_key = node._make_key(test_key)
            
            # Use put method
            node.put(test_key, test_data)
            
            # Use get method
            value = node.get(test_key)
            
            # Check that we got the right data
            assert value == test_data
            
            # Test get with non-existent key
            value = node.get("nonexistent")
            assert value is None
        finally:
            node.stop()
    
    def test_take(self):
        """Test the take method."""
        node = TestNode()
        
        try:
            # Set up test data directly
            key = "testbot/test/data"
            node._latest_values[key] = "test_value"
            
            # Take the value
            value = node.take("data")
            assert value == "test_value"
            
            # Value should be consumed
            assert node._latest_values[key] is None
            
            # Second take should return None
            value = node.take("data")
            assert value is None
            
            # Non-existent key should return None
            value = node.take("nonexistent")
            assert value is None
        finally:
            node.stop()
    
    def test_subscribe(self):
        """Test subscribing to topics."""
        node = TestNode()
        
        try:
            # Test key and data
            test_key = "test/subscribe"
            test_data = "test_value"
            full_key = node._make_key(test_key)
            
            # Keep track of received data
            received_data = None
            
            def on_data(data):
                nonlocal received_data
                received_data = data
            
            # Subscribe
            node.subscribe(test_key, on_data)
            
            # Publish data
            node.session.put(full_key, test_data)
            
            # Give a small delay to ensure callback is processed
            time.sleep(0.01)
            
            # Check data was received
            assert received_data == test_data
        finally:
            node.stop() 