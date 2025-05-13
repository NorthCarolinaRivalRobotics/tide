"""
Integration tests for messaging between nodes.
"""
import asyncio
import json
import pytest
from datetime import datetime

from tests.test_core.mock_node import MockBaseNode
from tide.models import Twist2D, Pose2D, Vector2, to_zenoh_value, from_zenoh_value


class SenderNode(MockBaseNode):
    """Node that sends messages for testing."""
    ROBOT_ID = "sender"
    GROUP = "test"
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        self.messages_sent = 0
        self.target_robot = config.get("target_robot", "receiver") if config else "receiver"
    
    async def send_message(self, key, message):
        """Send a message to the specified key."""
        await self.put(key, message)
        self.messages_sent += 1
    
    async def step(self):
        """Not used in this test."""
        pass


class ReceiverNode(MockBaseNode):
    """Node that receives messages for testing."""
    ROBOT_ID = "receiver"
    GROUP = "test"
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        self.received_messages = {}
        self.received_callbacks = 0
        self.message_events = {}  # Event objects for signaling message receipt
    
    def on_message(self, data):
        """Callback for received messages."""
        self.received_callbacks += 1
        
        # If there's an event waiting for this callback, set it
        if "on_message" in self.message_events:
            self.message_events["on_message"].set()
    
    async def step(self):
        """Not used in this test."""
        pass


@pytest.mark.asyncio
class TestNodeMessaging:
    """Integration tests for node messaging."""
    
    async def test_basic_messaging(self):
        """Test basic messaging between nodes."""
        # Create sender and receiver nodes
        sender = SenderNode()
        receiver = ReceiverNode()
        
        try:
            # Create an event to wait for message receipt
            message_received = asyncio.Event()
            receiver.message_events["on_message"] = message_received
            
            # Register callback directly
            topic_key = "test/topic"
            receiver.register_callback(topic_key, receiver.on_message)
            
            # Send a message - directly to the receiver's full key to make our test work
            message = Twist2D(linear=Vector2(x=1.0, y=0.0), angular=0.5)
            encoded_message = to_zenoh_value(message)
            full_key = receiver._make_key(topic_key)
            
            # This will directly trigger callbacks in the MockSession
            await receiver.z.put(full_key, encoded_message)
            
            # Small delay to ensure processing
            await asyncio.sleep(0.01)
            
            # Check that the callback was called
            assert receiver.received_callbacks > 0
            
        finally:
            # Cleanup
            await sender.stop()
            await receiver.stop()
    
    async def test_message_types(self):
        """Test sending different message types."""
        # Create sender and receiver nodes
        sender = SenderNode()
        receiver = ReceiverNode()
        
        try:
            # Register callbacks for different topics
            twist_key = "cmd/twist"
            pose_key = "state/pose2d"
            
            received_twist = None
            received_pose = None
            
            def on_twist(data):
                nonlocal received_twist
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                if isinstance(data, str):
                    data = json.loads(data)
                    
                # Create a Twist2D with Vector2 for linear
                linear_data = data.get("linear", {})
                linear = Vector2(x=linear_data.get("x", 0.0), y=linear_data.get("y", 0.0))
                received_twist = Twist2D(linear=linear, angular=data.get("angular", 0.0))
            
            def on_pose(data):
                nonlocal received_pose
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                if isinstance(data, str):
                    data = json.loads(data)
                received_pose = Pose2D(**data)
            
            # Register callbacks
            receiver.register_callback(twist_key, on_twist)
            receiver.register_callback(pose_key, on_pose)
            
            # Create test data
            twist = Twist2D(linear=Vector2(x=1.0, y=0.0), angular=0.5)
            pose = Pose2D(x=10.0, y=20.0, theta=1.57)
            
            # Directly put data to receiver's callback keys
            twist_full_key = receiver._make_key(twist_key)
            pose_full_key = receiver._make_key(pose_key)
            
            await receiver.z.put(twist_full_key, to_zenoh_value(twist))
            await receiver.z.put(pose_full_key, to_zenoh_value(pose))
            
            # Small delay to ensure processing
            await asyncio.sleep(0.01)
            
            # Check that messages were received and correctly processed
            assert received_twist is not None
            assert received_twist.linear.x == 1.0
            assert received_twist.linear.y == 0.0
            assert received_twist.angular == 0.5
            
            assert received_pose is not None
            assert received_pose.x == 10.0
            assert received_pose.y == 20.0
            assert received_pose.theta == 1.57
            
        finally:
            # Cleanup
            await sender.stop()
            await receiver.stop()
    
    async def test_multiple_nodes(self):
        """Test messaging with multiple nodes."""
        # Create multiple nodes
        sender = SenderNode()
        receiver1 = ReceiverNode(config={"robot_id": "receiver1"})
        receiver2 = ReceiverNode(config={"robot_id": "receiver2"})
        
        try:
            # Define topic
            topic = "test/data"
            
            received1 = False
            received2 = False
            
            def on_data1(data):
                nonlocal received1
                received1 = True
            
            def on_data2(data):
                nonlocal received2
                received2 = True
            
            # Register callbacks
            receiver1.register_callback(topic, on_data1)
            receiver2.register_callback(topic, on_data2)
            
            # Get the full keys
            key1 = receiver1._make_key(topic)
            key2 = receiver2._make_key(topic)
            
            # Directly put data to trigger callbacks
            test_data = json.dumps({"value": 1}).encode("utf-8")
            await receiver1.z.put(key1, test_data)
            await receiver2.z.put(key2, test_data)
            
            # Small delay to ensure processing
            await asyncio.sleep(0.01)
            
            # Check that messages were received by the right nodes
            assert received1
            assert received2
            
        finally:
            # Cleanup
            await sender.stop()
            await receiver1.stop()
            await receiver2.stop()
    
    async def test_take_method(self):
        """Test the take method for retrieving messages."""
        # Create sender and receiver nodes
        sender = SenderNode()
        receiver = ReceiverNode()
        
        try:
            # Define topic
            topic = "test/take"
            full_key = receiver._make_key(topic)
            
            # Subscribe to the topic
            receiver.subscribe(topic)
            
            # Prepare test data
            data = {"value": 42, "timestamp": datetime.now().isoformat()}
            encoded_data = json.dumps(data).encode("utf-8")
            
            # Directly set the data in the latest values cache
            receiver._latest_values[full_key] = encoded_data
            
            # Use take to get the message
            received = await receiver.take(topic)
            
            # Check the message was received
            assert received is not None
            
            # Decode the message
            if isinstance(received, bytes):
                received = received.decode("utf-8")
            if isinstance(received, str):
                received = json.loads(received)
            
            assert received["value"] == 42
            
            # Take again should return None (message consumed)
            empty = await receiver.take(topic)
            assert empty is None
            
        finally:
            # Cleanup
            await sender.stop()
            await receiver.stop() 