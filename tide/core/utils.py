import importlib
import importlib.util
import os
from typing import Any, Dict, List, Mapping, Type, Optional, Union


from tide.core.node import BaseNode
from tide.config import TideConfig

def import_class(class_path: str) -> Type:
    """
    Dynamically import a class from a string path.
    
    Args:
        class_path: String in format 'module.submodule.ClassName'
        
    Returns:
        The imported class
    """
    module_path, class_name = class_path.rsplit('.', 1)
    
    # First try to import with the current path (for project-local imports)
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError:
        # If that fails, try with the tide. prefix (for framework modules)
        try:
            module = importlib.import_module(f"tide.{module_path}")
            return getattr(module, class_name)
        except ImportError:
            # As a last resort, try importing directly
            # This is useful for files in the current directory
            full_path = module_path.replace('.', '/')
            if os.path.exists(f"{full_path}.py"):
                spec = importlib.util.spec_from_file_location(module_path, f"{full_path}.py")
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return getattr(module, class_name)
            
            # If we get here, we couldn't find the module
            raise

def create_node(node_type: str, params: Dict[str, Any] = None) -> BaseNode:
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

def launch_from_config(config: Union[TideConfig, Mapping[str, Any]]) -> List[BaseNode]:
    """Launch a set of nodes from a configuration object or mapping."""

    cfg = config if isinstance(config, TideConfig) else TideConfig.model_validate(config)

    nodes: List[BaseNode] = []

    # Configure session (placeholder for future extensions)
    _session_cfg = cfg.session

    # Create nodes
    for node_cfg in cfg.nodes:
        node = create_node(node_cfg.type, node_cfg.params)
        node.start()
        nodes.append(node)
        
    return nodes
