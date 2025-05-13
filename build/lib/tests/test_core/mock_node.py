"""
Mock implementation of the BaseNode class for testing.
"""
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable


class MockSample:
    """Mock sample for zenoh tests."""
    def __init__(self, value: Any):
        self.payload = value


class MockReply:
    """Mock reply for zenoh get operations."""
    class OkReply:
        def __init__(self, key_expr, value):
            self.key_expr = key_expr
            self.payload = value
            
    def __init__(self, key, value):
        self.ok = self.OkReply(key, value)


class MockPublisher:
    """Mock publisher for zenoh tests."""
    def __init__(self, session, key):
        self.session = session
        self.key = key
        
    def put(self, value: Any) -> None:
        """Publish value using the session."""
        self.session.internal_put(self.key, value)
        
    def undeclare(self):
        """Clean up publisher resources."""
        pass


class MockSubscription:
    """Mock subscription for zenoh tests."""
    def __init__(self, parent, key, callback):
        self.parent = parent
        self.key = key
        self.callback = callback
        
    def undeclare(self):
        """Remove this subscription."""
        if self.key in self.parent._subscriptions:
            if self.callback in self.parent._subscriptions[self.key]:
                self.parent._subscriptions[self.key].remove(self.callback)


class MockSession:
    """Mock zenoh session for testing."""
    def __init__(self):
        self.id = "mock-session-id"
        self._data = {}
        self._subscriptions = {}
        self._publishers = {}
    
    def internal_put(self, key: str, value: Any) -> None:
        """Internal method to store data and trigger subscriptions."""
        # Store the value
        self._data[key] = value
        
        # Trigger any subscriptions for this key
        if key in self._subscriptions:
            for callback in self._subscriptions[key]:
                callback(MockSample(value))
    
    def put(self, key: str, value: Any) -> None:
        """
        Backward compatibility for tests - directly publish without a publisher.
        This simulates the old API pattern for easier testing.
        """
        self.internal_put(key, value)
        
    def declare_publisher(self, key: str) -> MockPublisher:
        """Declare a publisher for a key."""
        pub = MockPublisher(self, key)
        self._publishers[key] = pub
        return pub
    
    def get(self, key: str):
        """Get data for a key."""
        class MockReplies:
            def __init__(self, replies):
                self.replies = replies
            
            def __iter__(self):
                return iter(self.replies)
        
        if key in self._data:
            return MockReplies([MockReply(key, self._data[key])])
        return MockReplies([])
    
    def declare_subscriber(self, key: str, callback: Callable) -> MockSubscription:
        """Declare a subscriber for a key."""
        if key not in self._subscriptions:
            self._subscriptions[key] = []
        
        self._subscriptions[key].append(callback)
        return MockSubscription(self, key, callback)
        
    def subscribe(self, key: str, callback: Callable) -> MockSubscription:
        """Backward compatibility for tests - old style subscribe method."""
        return self.declare_subscriber(key, callback)
    
    def close(self) -> None:
        """Clean up resources."""
        self._data = {}
        self._subscriptions = {}
        self._publishers = {}


def mock_open(config=None):
    """Mock for zenoh.open."""
    return MockSession()


class MockBaseNode(ABC):
    """
    Mock version of the BaseNode class for testing.
    
    Mimics the behavior of the real BaseNode but uses a mock zenoh session.
    """
    ROBOT_ID: str = "robot"  # Override in derived classes or set in config
    GROUP: str = ""          # Override in derived classes
    
    hz: float = 50.0         # Default update rate

    def __init__(self, *, config: Dict[str, Any] = None):
        """
        Initialize a node with configuration parameters.
        
        Args:
            config: Dictionary of configuration parameters
        """
        self.session = MockSession()
        
        self.config = config or {}
        
        # Override ROBOT_ID from config if provided
        if "robot_id" in self.config:
            self.ROBOT_ID = self.config["robot_id"]
            
        self.threads: List[threading.Thread] = []
        self._subscribers = {}
        self._publishers = {}
        self._callbacks = {}
        self._latest_values = {}
        self._running = False

    def _make_key(self, key: str) -> str:
        """
        Create a fully qualified key with the node's robot ID and group.
        
        Args:
            key: Topic key (e.g. "cmd/twist")
            
        Returns:
            Full key path (e.g. "robot/cmd/twist")
            
        Note:
            Modern Zenoh API does not allow leading slashes in key expressions.
        """
        # Check if originally had a leading slash (absolute path indicator)
        is_absolute = key.startswith('/')
        
        # Remove any leading or trailing slashes
        key = key.strip('/')
        
        # If it was an absolute path, return without prefixes
        if is_absolute:
            return key
            
        # If group is specified in the class and not in the key, add it
        if self.GROUP and not key.startswith(f"{self.GROUP}/"):
            return f"{self.ROBOT_ID}/{self.GROUP}/{key}"
            
        return f"{self.ROBOT_ID}/{key}"

    def put(self, key: str, value: Any) -> None:
        """
        Publish a value to a Zenoh key.
        
        Args:
            key: Topic key (will be prefixed with ROBOT_ID and GROUP)
            value: Value to publish (will be serialized)
        """
        full_key = self._make_key(key)
        
        # Get or create a publisher for this key
        if full_key not in self._publishers:
            self._publishers[full_key] = self.session.declare_publisher(full_key)
            
        # Publish the value
        self._publishers[full_key].put(value)

    def get(self, key: str) -> Optional[Any]:
        """
        Get the latest value for a key.
        
        Args:
            key: Topic key to query
            
        Returns:
            The latest value or None if not available
        """
        full_key = self._make_key(key)
        replies = self.session.get(full_key)
        
        for reply in replies:
            if hasattr(reply, 'ok'):
                return reply.ok.payload
                
        return None

    def take(self, key: str) -> Optional[Any]:
        """
        Non-blocking get of the latest value for a key.
        
        Args:
            key: Topic key
            
        Returns:
            The latest cached value or None if not available
        """
        full_key = self._make_key(key)
        if full_key in self._latest_values:
            value = self._latest_values[full_key]
            self._latest_values[full_key] = None  # Consume the value
            return value
        return None

    def subscribe(self, key: str, callback: Optional[Callable[[Any], None]] = None) -> None:
        """
        Subscribe to a key and store received values.
        
        Args:
            key: Topic key to subscribe to
            callback: Optional callback for received values
        """
        full_key = self._make_key(key)
        
        def _on_sample(sample):
            # Store the latest value
            self._latest_values[full_key] = sample.payload
            
            # Call the direct callback if provided
            if callback:
                callback(sample.payload)
                
            # Call any registered callbacks for this key
            if full_key in self._callbacks:
                for cb in self._callbacks[full_key]:
                    cb(sample.payload)
        
        # Declare a subscriber with the callback
        sub = self.session.declare_subscriber(full_key, _on_sample)
        self._subscribers[full_key] = sub
        
    def register_callback(self, key: str, callback: Callable[[Any], None]) -> None:
        """
        Register a callback function for a specific key.
        
        Args:
            key: Topic key
            callback: Function to call when data is received
        """
        full_key = self._make_key(key)
        
        # Create entry for this key if it doesn't exist
        if full_key not in self._callbacks:
            self._callbacks[full_key] = []
            
        # Add callback
        self._callbacks[full_key].append(callback)
        
        # Ensure we're subscribed to this key
        if full_key not in self._subscribers:
            self.subscribe(key)

    @abstractmethod
    def step(self) -> None:
        """
        Main processing loop, called at the node's update rate.
        Must be implemented by derived classes.
        """
        pass

    def run(self) -> None:
        """Run the node's main loop at the specified rate."""
        self._running = True
        last_time = time.time()
        
        while self._running:
            self.step()
            
            # Sleep for the remaining time to maintain hz rate
            elapsed = time.time() - last_time
            sleep_time = max(0, (1.0 / self.hz) - elapsed)
            time.sleep(sleep_time)
            last_time = time.time()
    
    def start(self) -> threading.Thread:
        """Start the node as a thread."""
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        self.threads.append(thread)
        return thread
    
    def stop(self) -> None:
        """Stop the node and clean up resources."""
        self._running = False
        
        # Wait for all threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
            
        # Clean up subscribers and publishers
        for sub in self._subscribers.values():
            sub.undeclare()
            
        for pub in self._publishers.values():
            pub.undeclare()
            
        # Close zenoh session
        self.session.close() 