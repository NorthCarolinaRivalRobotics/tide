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
        
        # Subscribe to pong responses using the namespace that PongNode is publishing to
        self.subscribe("/pong/pong/pong", self._on_pong)
        
    def _on_pong(self, sample):
        """Handle incoming pong messages."""
        try:
            print(f"Ping node received pong: {sample}")
            # Increment counter
            self.pong_received_count += 1
            
            # Try to extract payload data
            if hasattr(sample, 'payload'):
                # Try to decode and extract ping_id if available
                try:
                    payload_str = sample.payload.decode('utf-8') if hasattr(sample.payload, 'decode') else str(sample.payload)
                    self.last_pong_id = payload_str
                    print(f"Decoded pong payload: {payload_str}")
                except Exception as e:
                    print(f"Could not decode payload: {e}")
        except Exception as e:
            print(f"Error processing pong message: {e}")
    
    def send_ping(self):
        """Send a ping message."""
        self.ping_count += 1
        ping_msg = f"ping #{self.ping_count}"
        self.put("ping", ping_msg)
        print(f"Ping node published: {ping_msg}")
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
        
        # Subscribe to ping messages - need to use the exact key that PingNode is publishing to
        self.subscribe("/ping/ping/ping", self._on_ping)
    
    def _on_ping(self, sample):
        """Handle incoming ping messages and respond with a pong."""
        try:
            print(f"Pong node received ping: {sample}")
            self.ping_received_count += 1
            
            # Send a pong in response
            self.pong_count += 1
            pong_msg = f"pong #{self.pong_count} with ping_id: {self.ping_received_count}"
            self.put("pong", pong_msg)
            print(f"Pong node sent response: {pong_msg}")
        except Exception as e:
            print(f"Error processing ping message: {e}")
    
    def step(self):
        """No continuous operation in this test node."""
        pass


class TestPingPong:
    """Integration tests for ping-pong communication between nodes."""
    
    def test_ping_pong_communication(self):
        """Test that ping and pong nodes can communicate with each other."""
        # Create the nodes with explicit robot IDs
        ping_node = PingNode(config={"robot_id": "ping"})
        pong_node = PongNode(config={"robot_id": "pong"})
        
        # Start the nodes
        ping_thread = ping_node.start()
        pong_thread = pong_node.start()
        
        # Wait for nodes to initialize and establish subscriptions
        time.sleep(1.0)
        
        # Print debugging info about the subscriptions
        print(f"Ping node subscribers: {list(ping_node._subscribers.keys())}")
        print(f"Pong node subscribers: {list(pong_node._subscribers.keys())}")
        
        # Send several pings with longer delays between them
        for i in range(3):
            ping_msg = ping_node.send_ping()
            # Give enough time for the message to be received and processed
            time.sleep(1.0)
        
        # Give extra time for final messages to propagate
        time.sleep(1.0)
        
        # Verify communication occurred
        print(f"Ping count: {ping_node.ping_count}")
        print(f"Pings received by pong node: {pong_node.ping_received_count}")
        print(f"Pongs received by ping node: {ping_node.pong_received_count}")
        
        # Clean up
        ping_node.stop()
        pong_node.stop()
        
        # Wait for threads to finish
        ping_thread.join(timeout=1.0)
        pong_thread.join(timeout=1.0)
        
        # Final assertions
        assert ping_node.ping_count == 3, "Should have sent 3 pings"
        assert pong_node.ping_received_count > 0, "Pong node should have received at least one ping"
        assert ping_node.pong_received_count > 0, "Ping node should have received at least one pong" 