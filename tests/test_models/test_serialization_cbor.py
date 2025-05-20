import pytest
from tide.models import Pose2D, encode_message, decode_message, to_zenoh_value, from_zenoh_value


def test_cbor_helpers_roundtrip():
    msg = Pose2D(x=1.0, y=2.0, theta=0.5)
    data = encode_message(msg)
    restored = decode_message(data, Pose2D)
    assert restored == msg


def test_to_from_zenoh_value_roundtrip():
    msg = Pose2D(x=3.0, y=4.0, theta=1.2)
    data = to_zenoh_value(msg)
    restored = from_zenoh_value(data, Pose2D)
    assert restored == msg


def test_message_methods():
    msg = Pose2D(x=5.0, y=6.0, theta=2.0)
    data = msg.to_bytes()
    restored = Pose2D.from_bytes(data)
    assert restored == msg
