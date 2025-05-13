import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable

import zenoh

class BaseNode(ABC):
    """
    Base class for all robot nodes in the tide framework.
    
    Each node runs an asyncio task that communicates over a shared Zenoh session.
    Keys follow an opinionated pattern of /{robot_id}/{group}/{topic}
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
        self.z = zenoh.open()   # One session per process
        self.config = config or {}
        
        # Override ROBOT_ID from config if provided
        if "robot_id" in self.config:
            self.ROBOT_ID = self.config["robot_id"]
            
        self.tasks: List[asyncio.Task] = []
        self._subscribers = {}
        self._callbacks = {}
        self._latest_values = {}
        self._running = False

    def _make_key(self, key: str) -> str:
        """
        Create a fully qualified key with the node's robot ID and group.
        
        Args:
            key: Topic key (e.g. "cmd/twist")
            
        Returns:
            Full key path (e.g. "/robot/cmd/twist")
        """
        if key.startswith('/'):
            return key
            
        # If group is specified in the class and not in the key, add it
        if self.GROUP and not key.startswith(f"{self.GROUP}/"):
            return f"/{self.ROBOT_ID}/{self.GROUP}/{key}"
            
        return f"/{self.ROBOT_ID}/{key}"

    async def put(self, key: str, value: Any) -> None:
        """
        Publish a value to a Zenoh key.
        
        Args:
            key: Topic key (will be prefixed with ROBOT_ID and GROUP)
            value: Value to publish (will be serialized)
        """
        full_key = self._make_key(key)
        await self.z.put(full_key, value)

    async def get(self, key: str) -> Optional[Any]:
        """
        Get the latest value for a key.
        
        Args:
            key: Topic key to query
            
        Returns:
            The latest value or None if not available
        """
        full_key = self._make_key(key)
        samples = await self.z.get(full_key)
        for sample in samples:
            return sample.value
        return None

    async def take(self, key: str) -> Optional[Any]:
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
            self._latest_values[full_key] = sample.value
            if callback:
                callback(sample.value)
                
            # Call any registered callbacks for this key
            if full_key in self._callbacks:
                for cb in self._callbacks[full_key]:
                    cb(sample.value)
                
        sub = self.z.subscribe(full_key, _on_sample)
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
    async def step(self) -> None:
        """
        Main processing loop, called at the node's update rate.
        Must be implemented by derived classes.
        """
        pass

    async def run(self) -> None:
        """Run the node's main loop at the specified rate."""
        self._running = True
        last_time = time.time()
        
        while self._running:
            await self.step()
            
            # Sleep for the remaining time to maintain hz rate
            elapsed = time.time() - last_time
            sleep_time = max(0, (1.0 / self.hz) - elapsed)
            await asyncio.sleep(sleep_time)
            last_time = time.time()
    
    def start(self) -> asyncio.Task:
        """Start the node as an asyncio task."""
        task = asyncio.create_task(self.run())
        self.tasks.append(task)
        return task
    
    async def stop(self) -> None:
        """Stop the node and clean up resources."""
        self._running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
            
        # Clean up subscribers
        for sub in self._subscribers.values():
            sub.close()
            
        # Close zenoh session
        self.z.close() 