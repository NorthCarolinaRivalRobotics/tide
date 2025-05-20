import json
from pydantic import BaseModel

from tide.models.serialization import to_json, to_dict, to_zenoh_value, from_zenoh_value


class DummyModel(BaseModel):
    x: int
    y: str


def test_serialization_roundtrip():
    obj = DummyModel(x=1, y="a")
    json_str = to_json(obj)
    data = json.loads(json_str)
    assert data == {"x": 1, "y": "a"}

    as_dict = to_dict(obj)
    assert as_dict == {"x": 1, "y": "a"}

    val = to_zenoh_value(obj)
    assert isinstance(val, bytes)

    restored = from_zenoh_value(val, DummyModel)
    assert restored == obj


def test_from_zenoh_value_dict():
    data = {"a": 1}
    val = to_zenoh_value(data)
    restored = from_zenoh_value(val, dict)
    assert restored == data
