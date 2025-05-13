import time
import pytest
from tide.core.node import BaseNode

class PingNode(BaseNode):
    """A node that sends ping messages and listens for pong responses."""
    GROUP = "ping"
    
    def __init__(self, config=None):
        super().__init__(config=config)
        self.ping_count = 0
        self.pong_received_count = 0
        self.last_pong_id = None
        
        # Subscribe to pong responses
        self.subscribe("pong", self._on_pong)
        
    def _on_pong(self, sample):
        """Handle incoming pong messages."""
        try:
            if hasattr(sample, 'payload'):
                # Try to decode and extract ping_id if available
                payload_str = sample.payload.decode('utf-8') if hasattr(sample.payload, 'decode') else str(sample.payload)
                if "ping_id" in payload_str:
                    self.last_pong_id = payload_str
            
            # Increment counter regardless of format
            self.pong_received_count += 1
        except Exception as e:
            print(f"Error processing pong message: {e}")
    
    def send_ping(self):
        """Send a ping message."""
        self.ping_count += 1
        ping_msg = f"ping #{self.ping_count}"
        self.put("ping", ping_msg)
        return ping_msg
    
    def step(self):
        """No continuous operation in this test node."""
        pass


class PongNode(BaseNode):
    """A node that listens for ping messages and responds with pongs."""
    GROUP = "pong"
    
    def __init__(self, config=None):
        super().__init__(config=config)
        self.pong_count = 0
        self.ping_received_count = 0
        
        # Subscribe to ping messages
        self.subscribe("/ping/ping", self._on_ping)
    
    def _on_ping(self, sample):
        """Handle incoming ping messages and respond with a pong."""
        self.ping_received_count += 1
        
        # Send a pong in response
        self.pong_count += 1
        pong_msg = f"pong #{self.pong_count} with ping_id: {self.ping_received_count}"
        self.put("pong", pong_msg)
    
    def step(self):
        """No continuous operation in this test node."""
        pass


class TestPingPong:
    """Integration tests for ping-pong communication between nodes."""
    
    def test_ping_pong_communication(self):
        """Test that ping and pong nodes can communicate with each other."""
        # Create the nodes
        ping_node = PingNode(config={"robot_id": "ping"})
        pong_node = PongNode(config={"robot_id": "pong"})
        
        # Start the nodes
        ping_thread = ping_node.start()
        pong_thread = pong_node.start()
        
        # Wait a bit for nodes to initialize
        time.sleep(0.2)
        
        # Send several pings
        for i in range(3):
            ping_node.send_ping()
            # Give time for the message to be received and processed
            time.sleep(0.3)
        
        # Verify communication
        assert ping_node.ping_count == 3, "Should have sent 3 pings"
        assert pong_node.ping_received_count > 0, "Pong node should have received at least one ping"
        assert ping_node.pong_received_count > 0, "Ping node should have received at least one pong"
        
        # Clean up
        ping_node.stop()
        pong_node.stop()
        
        # Wait for threads to finish
        ping_thread.join(timeout=1.0)
        pong_thread.join(timeout=1.0)
        
        assert not ping_thread.is_alive(), "Ping thread should have stopped"
        assert not pong_thread.is_alive(), "Pong thread should have stopped" 