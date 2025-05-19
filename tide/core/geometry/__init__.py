from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Tuple

try:
    import numpy as np
except Exception:  # pragma: no cover - numpy may not be installed
    np = None  # type: ignore


def _ensure_numpy():
    if np is None:
        raise ImportError('numpy is required for tide.core.geometry')


def _skew(v: 'np.ndarray') -> 'np.ndarray':
    return np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0],
    ])


@dataclass
class Quaternion:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0

    @classmethod
    def from_euler(cls, roll: float, pitch: float, yaw: float) -> 'Quaternion':
        if np is None:
            cy = math.cos(yaw * 0.5)
            sy = math.sin(yaw * 0.5)
            cp = math.cos(pitch * 0.5)
            sp = math.sin(pitch * 0.5)
            cr = math.cos(roll * 0.5)
            sr = math.sin(roll * 0.5)

            w = cy * cp * cr + sy * sp * sr
            x = cy * cp * sr - sy * sp * cr
            y = sy * cp * sr + cy * sp * cr
            z = sy * cp * cr - cy * sp * sr
            return cls(x=x, y=y, z=z, w=w)
        else:
            cy = np.cos(yaw * 0.5)
            sy = np.sin(yaw * 0.5)
            cp = np.cos(pitch * 0.5)
            sp = np.sin(pitch * 0.5)
            cr = np.cos(roll * 0.5)
            sr = np.sin(roll * 0.5)
            w = cy * cp * cr + sy * sp * sr
            x = cy * cp * sr - sy * sp * cr
            y = sy * cp * sr + cy * sp * cr
            z = sy * cp * cr - cy * sp * sr
            return cls(float(x), float(y), float(z), float(w))

    def to_euler(self) -> Tuple[float, float, float]:
        if np is None:
            x, y, z, w = self.x, self.y, self.z, self.w
            sinr_cosp = 2 * (w * x + y * z)
            cosr_cosp = 1 - 2 * (x * x + y * y)
            roll = math.atan2(sinr_cosp, cosr_cosp)
            sinp = 2 * (w * y - z * x)
            if abs(sinp) >= 1:
                pitch = math.copysign(math.pi / 2, sinp)
            else:
                pitch = math.asin(sinp)
            siny_cosp = 2 * (w * z + x * y)
            cosy_cosp = 1 - 2 * (y * y + z * z)
            yaw = math.atan2(siny_cosp, cosy_cosp)
            return roll, pitch, yaw
        else:
            w, x, y, z = self.w, self.x, self.y, self.z
            sinr_cosp = 2 * (w * x + y * z)
            cosr_cosp = 1 - 2 * (x * x + y * y)
            roll = float(np.arctan2(sinr_cosp, cosr_cosp))
            sinp = 2 * (w * y - z * x)
            if abs(sinp) >= 1:
                pitch = float(np.copysign(math.pi / 2, sinp))
            else:
                pitch = float(np.arcsin(sinp))
            siny_cosp = 2 * (w * z + x * y)
            cosy_cosp = 1 - 2 * (y * y + z * z)
            yaw = float(np.arctan2(siny_cosp, cosy_cosp))
            return roll, pitch, yaw


class SO2:
    def __init__(self, theta: float):
        self.theta = float(theta)

    @classmethod
    def exp(cls, theta: float) -> 'SO2':
        return cls(theta)

    def log(self) -> float:
        return self.theta

    def as_matrix(self) -> 'np.ndarray':
        _ensure_numpy()
        c = np.cos(self.theta)
        s = np.sin(self.theta)
        return np.array([[c, -s], [s, c]])

    @classmethod
    def from_matrix(cls, m: 'np.ndarray') -> 'SO2':
        _ensure_numpy()
        theta = float(np.arctan2(m[1, 0], m[0, 0]))
        return cls(theta)


class SO3:
    def __init__(self, matrix: 'np.ndarray'):
        _ensure_numpy()
        self.matrix = np.asarray(matrix, dtype=float).reshape(3, 3)

    @classmethod
    def exp(cls, vec: 'np.ndarray') -> 'SO3':
        _ensure_numpy()
        vec = np.asarray(vec, dtype=float).reshape(3)
        theta = np.linalg.norm(vec)
        if theta < 1e-10:
            return cls(np.eye(3))
        k = vec / theta
        K = _skew(k)
        R = (
            np.eye(3)
            + np.sin(theta) * K
            + (1 - np.cos(theta)) * (K @ K)
        )
        return cls(R)

    def log(self) -> 'np.ndarray':
        _ensure_numpy()
        R = self.matrix
        theta = np.arccos(np.clip((np.trace(R) - 1) / 2.0, -1.0, 1.0))
        if theta < 1e-10:
            return np.zeros(3)
        vec = (
            theta
            / (2 * np.sin(theta))
            * np.array([
                R[2, 1] - R[1, 2],
                R[0, 2] - R[2, 0],
                R[1, 0] - R[0, 1],
            ])
        )
        return vec

    def as_matrix(self) -> 'np.ndarray':
        _ensure_numpy()
        return self.matrix

    @classmethod
    def from_matrix(cls, m: 'np.ndarray') -> 'SO3':
        return cls(m)


class SE2:
    def __init__(self, rotation: SO2, translation: 'np.ndarray'):
        _ensure_numpy()
        self.rotation = rotation
        self.translation = np.asarray(translation, dtype=float).reshape(2)

    @classmethod
    def exp(cls, vec: 'np.ndarray') -> 'SE2':
        _ensure_numpy()
        vec = np.asarray(vec, dtype=float).reshape(3)
        v = vec[:2]
        theta = vec[2]
        R = SO2.exp(theta)
        if abs(theta) < 1e-10:
            t = v
        else:
            V = np.array(
                [
                    [np.sin(theta) / theta, -(1 - np.cos(theta)) / theta],
                    [(1 - np.cos(theta)) / theta, np.sin(theta) / theta],
                ]
            )
            t = V @ v
        return cls(R, t)

    def log(self) -> 'np.ndarray':
        _ensure_numpy()
        theta = self.rotation.theta
        v = self.translation
        if abs(theta) < 1e-10:
            return np.array([v[0], v[1], 0.0])
        V_inv = (
            theta
            / (2 * (1 - np.cos(theta)))
            * np.array(
                [
                    [np.sin(theta), 1 - np.cos(theta)],
                    [-(1 - np.cos(theta)), np.sin(theta)],
                ]
            )
        )
        rho = V_inv @ v
        return np.array([rho[0], rho[1], theta])

    def as_matrix(self) -> 'np.ndarray':
        _ensure_numpy()
        R = self.rotation.as_matrix()
        t = self.translation
        M = np.eye(3)
        M[:2, :2] = R
        M[:2, 2] = t
        return M

    @classmethod
    def from_matrix(cls, m: 'np.ndarray') -> 'SE2':
        _ensure_numpy()
        R = SO2.from_matrix(m[:2, :2])
        t = m[:2, 2]
        return cls(R, t)


class SE3:
    def __init__(self, rotation: SO3, translation: 'np.ndarray'):
        _ensure_numpy()
        self.rotation = rotation
        self.translation = np.asarray(translation, dtype=float).reshape(3)

    @classmethod
    def exp(cls, vec: 'np.ndarray') -> 'SE3':
        _ensure_numpy()
        vec = np.asarray(vec, dtype=float).reshape(6)
        rho = vec[:3]
        phi = vec[3:]
        R = SO3.exp(phi)
        theta = np.linalg.norm(phi)
        if theta < 1e-10:
            V = np.eye(3)
        else:
            k = phi / theta
            K = _skew(k)
            V = (
                np.eye(3)
                + (1 - np.cos(theta)) / theta * K
                + (theta - np.sin(theta)) / theta * (K @ K)
            )
        t = V @ rho
        return cls(R, t)

    def log(self) -> 'np.ndarray':
        _ensure_numpy()
        phi = self.rotation.log()
        theta = np.linalg.norm(phi)
        if theta < 1e-10:
            V_inv = np.eye(3)
        else:
            k = phi / theta
            K = _skew(k)
            A = 1 - 0.5 * theta * np.tan(0.5 * theta)
            V_inv = (
                np.eye(3)
                - 0.5 * K
                + A * (K @ K)
            )
        rho = V_inv @ self.translation
        return np.concatenate([rho, phi])

    def as_matrix(self) -> 'np.ndarray':
        _ensure_numpy()
        M = np.eye(4)
        M[:3, :3] = self.rotation.as_matrix()
        M[:3, 3] = self.translation
        return M

    @classmethod
    def from_matrix(cls, m: 'np.ndarray') -> 'SE3':
        _ensure_numpy()
        R = SO3.from_matrix(m[:3, :3])
        t = m[:3, 3]
        return cls(R, t)


__all__ = ['Quaternion', 'SO2', 'SO3', 'SE2', 'SE3']
