import pytest
import math

np = pytest.importorskip("numpy")

from tide.core.geometry import _skew, Quaternion, SO2, SO3, SE2, SE3


def test_skew_matrix():
    v = np.array([1.0, 2.0, 3.0])
    expected = np.array([
        [0.0, -3.0, 2.0],
        [3.0, 0.0, -1.0],
        [-2.0, 1.0, 0.0],
    ])
    np.testing.assert_array_equal(_skew(v), expected)


def test_so2_matrix_roundtrip():
    theta = 0.123
    g = SO2.exp(theta)
    m = g.as_matrix()
    # reconstruct from matrix
    g2 = SO2.from_matrix(m)
    assert np.isclose(g2.log(), theta)
    np.testing.assert_allclose(m, g.as_matrix())


def test_so3_matrix_roundtrip():
    vec = np.array([0.1, -0.2, 0.3])
    g = SO3.exp(vec)
    m = g.as_matrix()
    g2 = SO3.from_matrix(m)
    np.testing.assert_allclose(g2.log(), vec, atol=1e-6)


def test_se2_matrix_roundtrip():
    vec = np.array([0.5, -0.4, 0.2])
    g = SE2.exp(vec)
    m = g.as_matrix()
    g2 = SE2.from_matrix(m)
    np.testing.assert_allclose(g2.log(), vec, atol=1e-6)


def test_se3_matrix_roundtrip():
    vec = np.array([0.1, -0.2, 0.3, 0.01, -0.02, 0.03])
    g = SE3.exp(vec)
    m = g.as_matrix()
    g2 = SE3.from_matrix(m)
    np.testing.assert_allclose(g2.log(), vec, atol=1e-6)


def test_small_angle_branches():
    # Zero rotation for SE2 and SE3 should follow the small angle branch
    se2 = SE2.exp(np.array([1.0, 2.0, 0.0]))
    np.testing.assert_allclose(se2.log(), np.array([1.0, 2.0, 0.0]))

    se3 = SE3.exp(np.array([1.0, 2.0, 3.0, 0.0, 0.0, 0.0]))
    np.testing.assert_allclose(se3.log(), np.array([1.0, 2.0, 3.0, 0.0, 0.0, 0.0]))


def test_quaternion_identity():
    q = Quaternion.from_euler(0.0, 0.0, 0.0)
    assert q == Quaternion(0.0, 0.0, 0.0, 1.0)
    r, p, y = q.to_euler()
    assert r == p == y == 0.0


def test_quaternion_normalization():
    g = SO3.exp(np.array([0.1, -0.2, 0.3]))
    q = g.to_quaternion()
    norm = math.sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w)
    assert abs(norm - 1.0) < 1e-6
    R = q.as_matrix()
    np.testing.assert_allclose(R @ R.T, np.eye(3), atol=1e-6)
    g2 = SO3.from_quaternion(q)
    np.testing.assert_allclose(g2.matrix, g.matrix)
