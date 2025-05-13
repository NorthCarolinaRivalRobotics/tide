import pytest
from tide.core.node import BaseNode

@pytest.fixture
def robot_config():
    """Fixture providing a standard robot configuration."""
    return {
        "robot_id": "test_robot"
    }

@pytest.fixture(autouse=True)
def cleanup_zenoh_sessions():
    """
    Fixture to ensure all Zenoh sessions are properly closed after each test.
    This helps prevent resource leaks between tests.
    """
    # Setup before test
    yield
    
    # Cleanup after test - nothing to do here as the BaseNode.stop() method
    # should properly clean up resources, but we could add additional cleanup
    # logic here if needed 