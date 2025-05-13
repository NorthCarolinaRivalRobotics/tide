"""
Simple test to verify Zenoh API integration with tide framework.
"""
import asyncio
import json
import time
from typing import Any

from tide.core.node import BaseNode

# Simple message for testing
class TestMessage:
    def __init__(self, value, timestamp=None):
        self.value = value
        self.timestamp = timestamp or time.time()
        
    def to_json(self):
        return json.dumps({
            "value": self.value,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(data["value"], data["timestamp"])


class Publisher(BaseNode):
    """
    Simple publisher node using the tide framework.
    """
    ROBOT_ID = "test_robot"
    GROUP = "test"

    def __init__(self):
        super().__init__()
        self.counter = 0
        
    async def publish_message(self):
        """Publish a single message."""
        msg = TestMessage(f"Message {self.counter}")
        
        # Encode as simple string
        encoded = msg.to_json().encode("utf-8")
        
        # Print what we're sending
        print(f"Publishing message #{self.counter}: {encoded!r}")
        
        # Publish to a test topic
        await self.put("data", encoded)
        
        # Increment counter
        self.counter += 1
        
        return msg.value

    async def step(self):
        """No auto-publishing in step."""
        pass


class Subscriber(BaseNode):
    """
    Simple subscriber node using the tide framework.
    """
    ROBOT_ID = "test_robot"  # Same robot ID to receive the messages
    GROUP = "test"

    def __init__(self):
        super().__init__()
        self.received_count = 0
        
        # Subscribe to the test topic
        self.subscribe("data", self.on_message)
        print(f"Subscribed to: {self._make_key('data')}")

    def on_message(self, data: Any):
        """Process received messages."""
        try:
            # Print raw data information for debugging
            print(f"\nReceived raw data of type: {type(data)}")
            print(f"Data representation: {data!r}")
            
            # Handle ZBytes format
            if str(type(data)) == "<class 'builtins.ZBytes'>":
                # Extract bytes from string representation
                data_str = str(data)
                print("Data is ZBytes, extracting bytes...")
                
                # Extract the byte values from string representation
                byte_values = []
                if "slices: [[" in data_str and "]]" in data_str:
                    hex_string = data_str.split("slices: [[")[1].split("]]")[0]
                    for hex_value in hex_string.split(", "):
                        if hex_value:
                            byte_values.append(int(hex_value, 16))
                
                if byte_values:
                    raw_bytes = bytes(byte_values)
                    decoded = raw_bytes.decode('utf-8')
                    print(f"Decoded ZBytes: {decoded}")
                    
                    # Try to parse as JSON
                    try:
                        msg = TestMessage.from_json(decoded)
                        self.received_count += 1
                        print(f"Successfully processed message #{self.received_count}: value={msg.value}")
                    except Exception as e:
                        print(f"Error parsing JSON: {e}")
            else:
                print("Unrecognized data format")
        
        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()

    async def step(self):
        """Nothing to do in step, just waiting for callbacks."""
        pass


async def main():
    """Run publisher and subscriber nodes."""
    print("Starting Zenoh test...")
    
    # Create a subscriber first
    sub = Subscriber()
    
    # Wait a moment for subscription to be set up
    await asyncio.sleep(1.0)
    print("Subscription ready")
    
    # Create a publisher
    pub = Publisher()
    
    try:
        # Run test loop - explicitly publish messages
        for i in range(10):
            # Publish a message
            value = await pub.publish_message()
            print(f"Published: {value}")
            
            # Wait a bit before next message
            await asyncio.sleep(1.0)
            print(f"Running test... {i+1}/10")
        
        # Give time for final message to be received
        await asyncio.sleep(0.5)
        
        # Check results
        print(f"\nSummary:")
        print(f"Published: {pub.counter} messages")
        print(f"Received: {sub.received_count} messages")
        
    finally:
        # Clean up
        await pub.stop()
        await sub.stop()
        print("Test completed")


if __name__ == "__main__":
    asyncio.run(main()) 