"""
Pytest configuration file with common fixtures for Tide framework tests.
"""
import asyncio
import pytest
from unittest.mock import MagicMock, patch
import zenoh
from typing import Dict, Any, Optional

from tide.core.node import BaseNode


class MockBaseNode(BaseNode):
    """
    Mock implementation of BaseNode for testing.
    Overrides the step method so it doesn't need to be implemented.
    """
    async def step(self):
        """Do nothing in the mock step method."""
        pass


@pytest.fixture
def mock_node():
    """Fixture providing a mock BaseNode instance."""
    # Mock zenoh.open to avoid actual network connections
    with patch('zenoh.open') as mock_open:
        # Create mock session
        mock_session = MagicMock()
        mock_open.return_value = mock_session
        
        # Setup common mock behaviors
        mock_session.get.return_value = []
        mock_session.subscribe.return_value = MagicMock()
        
        # Create the node
        node = MockBaseNode(config={"robot_id": "testbot"})
        yield node
        
        # Cleanup
        try:
            asyncio.run(node.stop())
        except RuntimeError:  # Raised when event loop is already closed
            pass


@pytest.fixture
def sample_config():
    """Fixture providing a sample node configuration."""
    return {
        "session": {
            "mode": "peer"
        },
        "nodes": [
            {
                "type": "test_module.TestNode",
                "params": {
                    "robot_id": "test_robot",
                    "param1": "value1",
                    "param2": 123
                }
            }
        ]
    }


@pytest.fixture
def mock_zenoh_data():
    """Fixture providing mock Zenoh data for testing."""
    class MockSample:
        def __init__(self, key, value):
            self.key = key
            self.value = value
    
    return MockSample(key="/testbot/test/key", value=b'{"test": "value"}')


# Helper to run async tests
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close() 