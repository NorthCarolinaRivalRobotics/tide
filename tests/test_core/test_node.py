"""
Tests for the BaseNode class and its functionality.
"""
import asyncio
import pytest
import time
from unittest.mock import MagicMock, patch

from tide.core.node import BaseNode
from tide.models import Twist2D, to_zenoh_value


class TestNode(BaseNode):
    """Simple test node implementation."""
    ROBOT_ID = "testbot"
    GROUP = "test"
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        self.step_called = False
        self.callback_called = False
        self.callback_data = None
    
    async def step(self):
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
        assert node._make_key("topic") == "/testbot/test/topic"
        
        # Test with absolute path
        assert node._make_key("/absolute/path") == "/absolute/path"
        
        # Test without GROUP
        node.GROUP = ""
        assert node._make_key("topic") == "/testbot/topic"
    
    @pytest.mark.asyncio
    async def test_register_callback(self, monkeypatch):
        """Test callback registration and invocation."""
        node = TestNode()
        
        # Mock the subscribe method
        orig_subscribe = node.subscribe
        subscribe_called = False
        
        def mock_subscribe(key, callback=None):
            nonlocal subscribe_called
            subscribe_called = True
            orig_subscribe(key, callback)
        
        monkeypatch.setattr(node, 'subscribe', mock_subscribe)
        
        # Register callback
        node.register_callback("data", node.test_callback)
        
        # Check that subscribe was called
        assert subscribe_called
        
        # Check callback is registered
        key = "/testbot/test/data"
        assert key in node._callbacks
        assert node.test_callback in node._callbacks[key]
        
        # Simulate receiving data
        mock_data = {"value": 42}
        # We use _on_sample directly to bypass the actual Zenoh subscription
        for sub_key, sub in node._subscribers.items():
            if sub_key == key:
                # Create a mock sample
                class MockSample:
                    def __init__(self, value):
                        self.value = value
                
                # Call the callback as if Zenoh triggered it
                node._subscribers[sub_key]._on_sample(MockSample(mock_data))
        
        # Check callback was called with data
        assert node.callback_called
        assert node.callback_data == mock_data
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping a node."""
        node = TestNode()
        
        # Start the node
        task = node.start()
        assert len(node.tasks) == 1
        assert task in node.tasks
        
        # Let it run briefly
        await asyncio.sleep(0.01)
        
        # Check that step was called
        assert node.step_called
        
        # Stop the node
        await node.stop()
        assert not node._running
        
        # Give it time to complete stopping
        await asyncio.sleep(0.01)
        
        # Check task status
        for task in node.tasks:
            assert task.done()
    
    @pytest.mark.asyncio
    async def test_put_get(self, monkeypatch):
        """Test putting and getting data."""
        node = TestNode()
        
        # Mock zenoh put and get methods
        put_key = None
        put_value = None
        
        async def mock_put(key, value):
            nonlocal put_key, put_value
            put_key = key
            put_value = value
        
        async def mock_get(key):
            class MockSamples:
                def __init__(self, samples):
                    self.samples = samples
                
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    if not self.samples:
                        raise StopAsyncIteration
                    return self.samples.pop(0)
            
            if key == "/testbot/test/data":
                class MockSample:
                    def __init__(self):
                        self.value = "test_value"
                
                return MockSamples([MockSample()])
            return MockSamples([])  # Empty samples for other keys
        
        monkeypatch.setattr(node.z, 'put', mock_put)
        monkeypatch.setattr(node.z, 'get', mock_get)
        
        # Test put
        await node.put("data", "test_data")
        assert put_key == "/testbot/test/data"
        assert put_value == "test_data"
        
        # Test get
        value = await node.get("data")
        assert value == "test_value"
        
        # Test get with non-existent key
        value = await node.get("nonexistent")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_take(self):
        """Test the take method."""
        node = TestNode()
        
        # Set up test data
        key = "/testbot/test/data"
        node._latest_values[key] = "test_value"
        
        # Take the value
        value = await node.take("data")
        assert value == "test_value"
        
        # Value should be consumed
        assert node._latest_values[key] is None
        
        # Second take should return None
        value = await node.take("data")
        assert value is None
        
        # Non-existent key should return None
        value = await node.take("nonexistent")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_subscribe(self, monkeypatch):
        """Test subscribing to topics."""
        node = TestNode()
        
        # Mock zenoh subscribe
        subscribe_key = None
        subscribe_callback = None
        class MockSubscription:
            def __init__(self):
                pass
            def close(self):
                pass
        
        def mock_subscribe(key, callback):
            nonlocal subscribe_key, subscribe_callback
            subscribe_key = key
            subscribe_callback = callback
            return MockSubscription()
        
        monkeypatch.setattr(node.z, 'subscribe', mock_subscribe)
        
        # Test subscribe
        callback = lambda x: x
        node.subscribe("data", callback)
        
        # Check key was processed correctly
        assert subscribe_key == "/testbot/test/data"
        
        # Check callback was stored
        assert subscribe_key in node._subscribers
        
        # Simulate receiving data
        class MockSample:
            def __init__(self, value):
                self.value = value
        
        # Invoke the callback
        subscribe_callback(MockSample("test_value"))
        
        # Check that data was stored
        assert node._latest_values[subscribe_key] == "test_value" 