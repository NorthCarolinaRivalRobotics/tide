"""
Integration tests for messaging between nodes.
"""
import asyncio
import pytest
from datetime import datetime

from tide.core.node import BaseNode
from tide.models import Twist2D, Pose2D, to_zenoh_value, from_zenoh_value


class SenderNode(BaseNode):
    """Node that sends messages for testing."""
    ROBOT_ID = "sender"
    GROUP = "test"
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        self.messages_sent = 0
        self.target_robot = config.get("target_robot", "receiver") if config else "receiver"
    
    async def send_message(self, key, message):
        """Send a message to the specified key."""
        await self.put(key, to_zenoh_value(message))
        self.messages_sent += 1
    
    async def step(self):
        """Not used in this test."""
        pass


class ReceiverNode(BaseNode):
    """Node that receives messages for testing."""
    ROBOT_ID = "receiver"
    GROUP = "test"
    
    def __init__(self, *, config=None):
        super().__init__(config=config)
        self.received_messages = {}
        self.received_callbacks = 0
    
    def on_message(self, data):
        """Callback for received messages."""
        self.received_callbacks += 1
    
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
            # Register callback for a topic
            topic_key = "test/topic"
            receiver.register_callback(topic_key, receiver.on_message)
            
            # Wait a bit for the subscription to be established
            await asyncio.sleep(0.5)
            
            # Send a message
            message = Twist2D(linear={"x": 1.0, "y": 0.0}, angular=0.5)
            await sender.send_message(f"/{receiver.ROBOT_ID}/{topic_key}", to_zenoh_value(message))
            
            # Wait a bit for the message to be received
            await asyncio.sleep(0.5)
            
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
                received_twist = from_zenoh_value(data, Twist2D)
            
            def on_pose(data):
                nonlocal received_pose
                received_pose = from_zenoh_value(data, Pose2D)
            
            receiver.register_callback(twist_key, on_twist)
            receiver.register_callback(pose_key, on_pose)
            
            # Wait a bit for the subscriptions to be established
            await asyncio.sleep(0.5)
            
            # Send messages
            twist = Twist2D(linear={"x": 1.0, "y": 0.0}, angular=0.5)
            pose = Pose2D(x=10.0, y=20.0, theta=1.57)
            
            await sender.send_message(f"/{receiver.ROBOT_ID}/{twist_key}", to_zenoh_value(twist))
            await sender.send_message(f"/{receiver.ROBOT_ID}/{pose_key}", to_zenoh_value(pose))
            
            # Wait a bit for the messages to be received
            await asyncio.sleep(0.5)
            
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
            # Register callbacks
            topic = "test/data"
            
            received1 = False
            received2 = False
            
            def on_data1(data):
                nonlocal received1
                received1 = True
            
            def on_data2(data):
                nonlocal received2
                received2 = True
            
            receiver1.register_callback(topic, on_data1)
            receiver2.register_callback(topic, on_data2)
            
            # Wait a bit for the subscriptions to be established
            await asyncio.sleep(0.5)
            
            # Send messages to specific receivers
            await sender.send_message(f"/receiver1/{topic}", to_zenoh_value({"value": 1}))
            await sender.send_message(f"/receiver2/{topic}", to_zenoh_value({"value": 2}))
            
            # Wait a bit for the messages to be received
            await asyncio.sleep(0.5)
            
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
            # Register subscription but don't use a callback
            topic = "test/take"
            key = f"/{receiver.ROBOT_ID}/{topic}"
            
            # Subscribe to the topic (no callback)
            receiver.subscribe(topic)
            
            # Wait a bit for the subscription to be established
            await asyncio.sleep(0.5)
            
            # Send a message
            data = {"value": 42, "timestamp": datetime.now().isoformat()}
            await sender.z.put(key, to_zenoh_value(data))
            
            # Wait a bit for the message to be received
            await asyncio.sleep(0.5)
            
            # Use take to get the message
            received = await receiver.take(topic)
            
            # Check the message was received
            assert received is not None
            
            # Decode the message
            decoded = from_zenoh_value(received, dict)
            assert decoded["value"] == 42
            
            # Take again should return None (message consumed)
            empty = await receiver.take(topic)
            assert empty is None
            
        finally:
            # Cleanup
            await sender.stop()
            await receiver.stop() 