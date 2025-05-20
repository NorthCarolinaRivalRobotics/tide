import json
from typing import Any, Dict, Type, TypeVar, Union

import cbor2

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
        return model.model_dump(mode="json")
    except (AttributeError, TypeError):
        # Try different approaches for non-models
        try:
            return vars(model)
        except (TypeError, ValueError):
            # Last resort
            return model.__dict__


def to_cbor(model: Union[BaseModel, Dict, Any]) -> bytes:
    """Convert a model or dictionary to CBOR bytes."""

    if isinstance(model, (bytes, bytearray)):
        return bytes(model)

    data = json.loads(to_json(model))
    return cbor2.dumps(data)


def from_cbor(data: Union[bytes, str, Any], model_class: Type[T]) -> T:
    """Decode CBOR data into a model instance.

    `data` may be a byte sequence, string, or any object implementing
    the ``__bytes__`` protocol (e.g., ``zenoh.ZBytes``).
    """

    if not isinstance(data, (bytes, bytearray)):
        if isinstance(data, str):
            data = data.encode("utf-8")
        else:
            try:
                data = bytes(data)
            except Exception:
                raise TypeError("Unsupported data type for CBOR decoding")

    obj = cbor2.loads(data)
    if model_class == dict:
        return obj

    try:
        return model_class.model_validate(obj)
    except (AttributeError, TypeError):
        inst = model_class()
        for k, v in obj.items():
            setattr(inst, k, v)
        return inst


def encode_message(msg: Union[BaseModel, Dict, Any]) -> bytes:
    """Convenience wrapper to encode a message to CBOR."""

    return to_cbor(msg)


def decode_message(data: Union[bytes, str], model_class: Type[T]) -> T:
    """Convenience wrapper to decode a message from CBOR."""

    return from_cbor(data, model_class)


def to_zenoh_value(model: Union[BaseModel, Dict, Any]) -> bytes:
    """
    Convert a model or data to bytes for Zenoh transport using CBOR.

    Args:
        model: Model or data to convert

    Returns:
        Bytes representation
    """
    return to_cbor(model)


def from_zenoh_value(data: Union[bytes, str], model_class: Type[T]) -> T:
    """Decode a Zenoh payload into the given model type using CBOR."""

    return from_cbor(data, model_class)
