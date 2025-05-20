import math
import pytest

import tide.core.geometry as geom


def test_quaternion_roundtrip_no_numpy():
    q = geom.Quaternion.from_euler(0.1, -0.2, 0.3)
    r, p, y = q.to_euler()
    assert math.isclose(r, 0.1, abs_tol=1e-6)
    assert math.isclose(p, -0.2, abs_tol=1e-6)
    assert math.isclose(y, 0.3, abs_tol=1e-6)


def test_ensure_numpy_raises(monkeypatch):
    monkeypatch.setattr(geom, "np", None)
    with pytest.raises(ImportError):
        geom._ensure_numpy()
