import pytest
from hypothesis import given, strategies as st

np = pytest.importorskip("numpy")

from tide.core.geometry import Quaternion, SO2, SO3, SE2, SE3


@given(st.floats(-0.5, 0.5), st.floats(-0.5, 0.5), st.floats(-0.5, 0.5))
def test_quaternion_roundtrip_prop(roll, pitch, yaw):
    q = Quaternion.from_euler(roll, pitch, yaw)
    r2, p2, y2 = q.to_euler()
    assert np.allclose([r2, p2, y2], [roll, pitch, yaw], atol=1e-6)


@given(st.floats(-0.5, 0.5))
def test_so2_roundtrip(theta):
    g = SO2.exp(theta)
    theta2 = g.log()
    assert np.isclose(theta2, theta, atol=1e-6)


@given(st.lists(st.floats(-0.5, 0.5), min_size=3, max_size=3))
def test_so3_roundtrip(vec_list):
    vec = np.array(vec_list)
    g = SO3.exp(vec)
    vec2 = g.log()
    assert np.allclose(vec2, vec, atol=1e-6)


@given(st.lists(st.floats(-0.5, 0.5), min_size=3, max_size=3))
def test_se2_roundtrip(vec_list):
    vec = np.array(vec_list)
    g = SE2.exp(vec)
    vec2 = g.log()
    assert np.allclose(vec2, vec, atol=1e-6)


@given(st.lists(st.floats(-0.3, 0.3), min_size=6, max_size=6))
def test_se3_roundtrip(vec_list):
    vec = np.array(vec_list)
    g = SE3.exp(vec)
    vec2 = g.log()
    assert np.allclose(vec2, vec, atol=1e-5)
