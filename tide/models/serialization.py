import json
from typing import Any, Dict, Type, TypeVar, Union

try:
    from pydantic import BaseModel
except ImportError:
    print("Pydantic not installed. Please install it with 'pip install pydantic'")
    # Provide fallback
    BaseModel = object

T = TypeVar('T', bound='BaseModel')

def to_json(model: BaseModel) -> str:
    """
    Convert a Pydantic model to JSON string.
    
    Args:
        model: Pydantic model to convert
        
    Returns:
        JSON string representation
    """
    try:
        return model.model_dump_json()
    except (AttributeError, TypeError):
        # Fallback if pydantic not available
        return json.dumps(vars(model))


def to_dict(model: BaseModel) -> Dict[str, Any]:
    """
    Convert a Pydantic model to a dictionary.
    
    Args:
        model: Pydantic model to convert
        
    Returns:
        Dictionary representation
    """
    try:
        return model.model_dump()
    except (AttributeError, TypeError):
        # Fallback if pydantic not available
        return vars(model)


def to_zenoh_value(model: BaseModel) -> bytes:
    """
    Convert a model to bytes for Zenoh transport.
    
    Args:
        model: Model to convert
        
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
    
    try:
        return model_class.model_validate(data)
    except (AttributeError, TypeError):
        # Fallback if pydantic not available
        obj = model_class()
        for k, v in data.items():
            setattr(obj, k, v)
        return obj 