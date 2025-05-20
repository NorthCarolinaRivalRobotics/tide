import threading
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable

import zenoh
from tide.models.serialization import encode_message, decode_message

class BaseNode(ABC):
    """
    Base class for all robot nodes in the tide framework.
    
    Each node runs as a thread that communicates over a shared Zenoh session.
    Keys follow an opinionated pattern of {robot_id}/{group}/{topic}
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
        self._stopping = False  # Flag to prevent multiple stop calls
        self._lock = threading.RLock()  # Lock for thread safety during cleanup
        
        # Initialize Zenoh session - simple approach that matches the working examples
        try:
            # Initialize logger to avoid excessive logging
            zenoh.init_log_from_env_or("error")
            self.session = zenoh.open(zenoh.Config())
            print(f"Successfully initialized Zenoh session for {self.__class__.__name__}")
        except ImportError:
            print(f"Error: Zenoh Python package not found. Please install with: uv add eclipse-zenoh")
            self.session = None
        except Exception as e:
            print(f"Error initializing Zenoh session: {e}")
            print("Make sure Zenoh is properly installed and configured.")
            self.session = None

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
        # Check if Zenoh session is initialized
        if self.session is None:
            print(f"Warning: Cannot publish to {key} - Zenoh session not initialized")
            return
            
        full_key = self._make_key(key)
        
        # Get or create a publisher for this key
        if full_key not in self._publishers:
            try:
                self._publishers[full_key] = self.session.declare_publisher(full_key)
            except Exception as e:
                print(f"Error creating publisher for {full_key}: {e}")
                return
        
        # Get the publisher
        publisher = self._publishers[full_key]
        if publisher is None:
            print(f"Warning: Publisher for {full_key} is None")
            return
            
        # Encode value if needed
        try:
            payload = encode_message(value)
        except Exception:
            payload = value

        try:
            publisher.put(payload)
        except Exception as e:
            print(f"Error publishing to {full_key}: {e}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get the latest value for a key.
        
        Args:
            key: Topic key to query
            
        Returns:
            The latest value or None if not available
        """
        # Check if Zenoh session is initialized
        if self.session is None:
            print(f"Warning: Cannot get {key} - Zenoh session not initialized")
            return None
            
        full_key = self._make_key(key)
        try:
            replies = self.session.get(full_key)
            
            for reply in replies:
                if hasattr(reply, 'ok'):
                    try:
                        return decode_message(reply.ok.payload, dict)
                    except Exception:
                        return reply.ok.payload
        except Exception as e:
            print(f"Error getting value for {full_key}: {e}")
            
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
            try:
                return decode_message(value, dict)
            except Exception:
                return value
        return None

    def subscribe(self, key: str, callback: Optional[Callable[[Any], None]] = None) -> None:
        """
        Subscribe to a key and store received values.
        
        Args:
            key: Topic key to subscribe to
            callback: Optional callback for received values
        """
        # Check if Zenoh session is initialized
        if self.session is None:
            print(f"Warning: Cannot subscribe to {key} - Zenoh session not initialized")
            return
            
        full_key = self._make_key(key)
        
        def _on_sample(sample):
            try:
                value = decode_message(sample.payload, dict)
            except Exception:
                value = sample

            # Store the latest value
            self._latest_values[full_key] = value
            
            # Call the direct callback if provided
            if callback:
                try:
                    callback(value)
                except Exception as e:
                    print(f"Error in callback for {full_key}: {e}")
                
            # Call any registered callbacks for this key
            if full_key in self._callbacks:
                for cb in self._callbacks[full_key]:
                    try:
                        cb(value)
                    except Exception as e:
                        print(f"Error in registered callback for {full_key}: {e}")
        
        # Declare a subscriber with the callback
        try:
            sub = self.session.declare_subscriber(full_key, _on_sample)
            self._subscribers[full_key] = sub
        except Exception as e:
            print(f"Error subscribing to {full_key}: {e}")

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
        # Create a thread for the node's run method
        thread = threading.Thread(target=self.run)
        thread.daemon = True  # Make thread exit when main program exits
        thread.start()
        self.threads.append(thread)
        
        # Return the thread so it can be joined by the caller if needed
        return thread
    
    def stop(self) -> None:
        """Stop the node and clean up resources."""
        with self._lock:
            # Prevent multiple stop calls
            if self._stopping:
                return
            self._stopping = True
            self._running = False
        
        # Wait for all threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)  # Give each thread 1 second to finish
        
        # Make a copy of resources to clean up to avoid modification during iteration
        subscribers_to_clean = list(self._subscribers.values())
        publishers_to_clean = list(self._publishers.values())
        
        # Clean up subscribers
        for sub in subscribers_to_clean:
            try:
                if sub is not None:
                    sub.undeclare()
            except Exception as e:
                # Just log the error, don't print it to avoid interrupting the shutdown
                logging.debug(f"Error undeclaring subscriber: {e}")
        
        # Clear the subscribers dictionary
        self._subscribers.clear()
        
        # Clean up publishers
        for pub in publishers_to_clean:
            try:
                if pub is not None:
                    pub.undeclare()
            except Exception as e:
                # Just log the error, don't print it to avoid interrupting the shutdown
                logging.debug(f"Error undeclaring publisher: {e}")
        
        # Clear the publishers dictionary
        self._publishers.clear()
        
        # Close zenoh session
        if self.session is not None:
            try:
                self.session.close()
            except Exception as e:
                logging.debug(f"Error closing Zenoh session: {e}")
            self.session = None 