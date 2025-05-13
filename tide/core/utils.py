import asyncio
import importlib
import math
from typing import Any, Dict, List, Type, Tuple, Optional

from tide.core.node import BaseNode

def import_class(class_path: str) -> Type:
    """
    Dynamically import a class from a string path.
    
    Args:
        class_path: String in format 'module.submodule.ClassName'
        
    Returns:
        The imported class
    """
    module_path, class_name = class_path.rsplit('.', 1)
    module = importlib.import_module(f"tide.{module_path}")
    return getattr(module, class_name)

async def create_node(node_type: str, params: Dict[str, Any] = None) -> BaseNode:
    """
    Create a node instance from a type string.
    
    Args:
        node_type: String path to node class (e.g. 'behaviors.TeleopNode')
        params: Configuration parameters for the node
        
    Returns:
        Instantiated node
    """
    node_class = import_class(node_type)
    return node_class(config=params)

async def launch_from_config(config: Dict[str, Any]) -> List[BaseNode]:
    """
    Launch a set of nodes from a configuration dictionary.
    
    Args:
        config: Dictionary with session and node configurations
        
    Returns:
        List of instantiated nodes
    """
    nodes = []
    
    # Configure session
    session_config = config.get("session", {})
    # TODO: Apply session configuration
    
    # Create nodes
    for node_config in config.get("nodes", []):
        node_type = node_config.get("type")
        params = node_config.get("params", {})
        
        node = await create_node(node_type, params)
        node.start()
        nodes.append(node)
        
    return nodes

def quaternion_from_euler(roll: float, pitch: float, yaw: float) -> Dict[str, float]:
    """
    Convert Euler angles to quaternion.
    
    Args:
        roll: Rotation around X axis (radians)
        pitch: Rotation around Y axis (radians)
        yaw: Rotation around Z axis (radians)
        
    Returns:
        Dictionary with quaternion components {x, y, z, w}
    """
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    
    q = {
        "w": cy * cp * cr + sy * sp * sr,
        "x": cy * cp * sr - sy * sp * cr,
        "y": sy * cp * sr + cy * sp * cr,
        "z": sy * cp * cr - cy * sp * sr
    }
    
    return q

def euler_from_quaternion(q: Dict[str, float]) -> Tuple[float, float, float]:
    """
    Convert quaternion to Euler angles.
    
    Args:
        q: Dictionary with quaternion components {x, y, z, w}
        
    Returns:
        Tuple of (roll, pitch, yaw) in radians
    """
    x, y, z, w = q["x"], q["y"], q["z"], q["w"]
    
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    
    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)  # Use 90 degrees if out of range
    else:
        pitch = math.asin(sinp)
    
    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    
    return (roll, pitch, yaw) 