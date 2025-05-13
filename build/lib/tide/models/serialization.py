import json
from typing import Any, Dict, Type, TypeVar, Union

try:
    from pydantic import BaseModel
except ImportError:
    print("Pydantic not installed. Please install it with 'pip install pydantic'")
    # Provide fallback
    BaseModel = object

T = TypeVar('T', bound='BaseModel')

def to_json(model: Union[BaseModel, Dict, Any]) -> str:
    """
    Convert a Pydantic model or dictionary to JSON string.
    
    Args:
        model: Pydantic model, dictionary, or other JSON-serializable object to convert
        
    Returns:
        JSON string representation
    """
    if isinstance(model, dict):
        return json.dumps(model)
    
    try:
        return model.model_dump_json()
    except (AttributeError, TypeError):
        # Try direct JSON serialization for non-models
        try:
            return json.dumps(model)
        except (TypeError, ValueError):
            # Fallback if pydantic not available and it's an object
            try:
                return json.dumps(vars(model))
            except (TypeError, ValueError):
                # Last resort - try with __dict__
                return json.dumps(model.__dict__)


def to_dict(model: Union[BaseModel, Dict]) -> Dict[str, Any]:
    """
    Convert a Pydantic model or dictionary to a dictionary.
    
    Args:
        model: Pydantic model or dictionary to convert
        
    Returns:
        Dictionary representation
    """
    if isinstance(model, dict):
        return model
    
    try:
        return model.model_dump()
    except (AttributeError, TypeError):
        # Try different approaches for non-models
        try:
            return vars(model)
        except (TypeError, ValueError):
            # Last resort
            return model.__dict__


def to_zenoh_value(model: Union[BaseModel, Dict, Any]) -> bytes:
    """
    Convert a model or data to bytes for Zenoh transport.
    
    Args:
        model: Model or data to convert
        
    Returns:
        Bytes representation
    """
    return to_json(model).encode('utf-8')


def from_zenoh_value(data: Union[bytes, str], model_class: Type[T]) -> T:
    """
    Create a model from Zenoh data.
    
    Args:
        data: Data received from Zenoh (bytes or string)
        model_class: Class of the model to create
        
    Returns:
        An instance of the model_class
    """
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    
    # If it's a string, parse it as JSON
    if isinstance(data, str):
        data = json.loads(data)
    
    # If model_class is dict, just return the data
    if model_class == dict:
        return data
    
    try:
        return model_class.model_validate(data)
    except (AttributeError, TypeError):
        # Fallback if pydantic not available
        obj = model_class()
        for k, v in data.items():
            setattr(obj, k, v)
        return obj 