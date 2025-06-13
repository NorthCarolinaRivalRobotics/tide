from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Tuple
import numpy as np

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
        return cls(x=x, y=y, z=z, w=w)


    def to_euler(self) -> Tuple[float, float, float]:
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

    def as_matrix(self) -> 'np.ndarray':
        """Convert quaternion to rotation matrix."""
        x, y, z, w = self.x, self.y, self.z, self.w
        norm = math.sqrt(x * x + y * y + z * z + w * w)
        if not math.isclose(norm, 1.0, abs_tol=1e-6):
            x /= norm
            y /= norm
            z /= norm
            w /= norm
        return np.array(
            [
                [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
            ]
        )



class SO2:
    def __init__(self, theta: float):
        self.theta = float(theta)

    @classmethod
    def exp(cls, theta: float) -> 'SO2':
        return cls(theta)

    def log(self) -> float:
        return self.theta

    def as_matrix(self) -> 'np.ndarray':
        c = np.cos(self.theta)
        s = np.sin(self.theta)
        return np.array([[c, -s], [s, c]])

    @classmethod
    def from_matrix(cls, m: 'np.ndarray') -> 'SO2':
        theta = float(np.arctan2(m[1, 0], m[0, 0]))
        return cls(theta)


class SO3:
    def __init__(self, matrix: 'np.ndarray'):
        self.matrix = np.asarray(matrix, dtype=float).reshape(3, 3)

    @classmethod
    def exp(cls, vec: 'np.ndarray') -> 'SO3':
        vec = np.asarray(vec, dtype=float).reshape(3)
        theta = np.linalg.norm(vec)
        if theta < 1e-6:
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
        R = self.matrix
        theta = np.arccos(np.clip((np.trace(R) - 1) / 2.0, -1.0, 1.0))
        if theta < 1e-6:
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

        return self.matrix

    def to_quaternion(self) -> 'Quaternion':
        """Convert this rotation to a quaternion."""
        m = self.matrix
        tr = m[0, 0] + m[1, 1] + m[2, 2]
        if tr > 0:
            s = 0.5 / np.sqrt(max(tr + 1.0, 0.0))
            w = 0.25 / s
            x = (m[2, 1] - m[1, 2]) * s
            y = (m[0, 2] - m[2, 0]) * s
            z = (m[1, 0] - m[0, 1]) * s
        else:
            if m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
                s = 2.0 * np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2])
                w = (m[2, 1] - m[1, 2]) / s
                x = 0.25 * s
                y = (m[0, 1] + m[1, 0]) / s
                z = (m[0, 2] + m[2, 0]) / s
            elif m[1, 1] > m[2, 2]:
                s = 2.0 * np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2])
                w = (m[0, 2] - m[2, 0]) / s
                x = (m[0, 1] + m[1, 0]) / s
                y = 0.25 * s
                z = (m[1, 2] + m[2, 1]) / s
            else:
                s = 2.0 * np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1])
                w = (m[1, 0] - m[0, 1]) / s
                x = (m[0, 2] + m[2, 0]) / s
                y = (m[1, 2] + m[2, 1]) / s
                z = 0.25 * s
        q = Quaternion(x=x, y=y, z=z, w=w)
        n = math.sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w)
        if n == 0:
            return q
        return Quaternion(x=q.x / n, y=q.y / n, z=q.z / n, w=q.w / n)

    @classmethod
    def from_matrix(cls, m: 'np.ndarray') -> 'SO3':
        return cls(m)

    @classmethod
    def from_quaternion(cls, q: 'Quaternion') -> 'SO3':
        """Create an SO3 from a quaternion."""
        return cls(q.as_matrix())


class SE2:
    def __init__(self, rotation: SO2, translation: 'np.ndarray'):
        
        self.rotation = rotation
        self.translation = np.asarray(translation, dtype=float).reshape(2)

    @classmethod
    def exp(cls, vec: 'np.ndarray') -> 'SE2':
        
        vec = np.asarray(vec, dtype=float).reshape(3)
        v = vec[:2]
        theta = vec[2]
        R = SO2.exp(theta)
        if abs(theta) < 1e-7:
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

    @staticmethod
    def identity() -> 'SE2':
        """Return the identity transformation."""
        return SE2(SO2.exp(0.0), np.zeros(2))

    def log(self) -> 'np.ndarray':
        theta = self.rotation.theta
        v = self.translation
        if abs(theta) < 1e-6:
            rho = v
        else:
            V = np.array(
                [
                    [np.sin(theta) / theta, -(1 - np.cos(theta)) / theta],
                    [(1 - np.cos(theta)) / theta, np.sin(theta) / theta],
                ]
            )
            rho = np.linalg.inv(V) @ v
        return np.array([rho[0], rho[1], theta])

    def as_matrix(self) -> 'np.ndarray':
        
        R = self.rotation.as_matrix()
        t = self.translation
        M = np.eye(3)
        M[:2, :2] = R
        M[:2, 2] = t
        return M

    @classmethod
    def from_matrix(cls, m: 'np.ndarray') -> 'SE2':
        
        R = SO2.from_matrix(m[:2, :2])
        t = m[:2, 2]
        return cls(R, t)

    def __mul__(self, other: 'SE2') -> 'SE2':
        """Group composition."""
        R1 = self.rotation.as_matrix()
        R2 = other.rotation.as_matrix()
        R = SO2.from_matrix(R1 @ R2)
        t = self.translation + R1 @ other.translation
        return SE2(R, t)

    def inverse(self) -> 'SE2':
        """Return the inverse transformation."""
        R_inv = self.rotation.as_matrix().T
        R = SO2.from_matrix(R_inv)
        t = -(R_inv @ self.translation)
        return SE2(R, t)


class SE3:
    def __init__(self, rotation: SO3, translation: 'np.ndarray'):
        
        self.rotation = rotation
        self.translation = np.asarray(translation, dtype=float).reshape(3)

    @classmethod
    def exp(cls, vec: 'np.ndarray') -> 'SE3':
        
        vec = np.asarray(vec, dtype=float).reshape(6)
        rho = vec[:3]
        phi = vec[3:]
        R = SO3.exp(phi)
        theta = np.linalg.norm(phi)
        if theta < 1e-6:
            V = np.eye(3)
        else:
            k = phi / theta
            K = _skew(k)
            V = (
                np.eye(3)
                + (1 - np.cos(theta)) / (theta ** 2) * K
                + (theta - np.sin(theta)) / (theta ** 3) * (K @ K)
            )
        t = V @ rho
        return cls(R, t)

    @staticmethod
    def identity() -> 'SE3':
        """Return the identity transformation."""
        return SE3(SO3.exp(np.zeros(3)), np.zeros(3))

    def log(self) -> 'np.ndarray':
        
        phi = self.rotation.log()
        theta = np.linalg.norm(phi)
        if theta < 1e-6:
            V_inv = np.eye(3)
        else:
            k = phi / theta
            K = _skew(k)
            V = (
                np.eye(3)
                + (1 - np.cos(theta)) / (theta ** 2) * K
                + (theta - np.sin(theta)) / (theta ** 3) * (K @ K)
            )
            V_inv = np.linalg.inv(V)
        rho = V_inv @ self.translation
        return np.concatenate([rho, phi])

    def as_matrix(self) -> 'np.ndarray':
        
        M = np.eye(4)
        M[:3, :3] = self.rotation.as_matrix()
        M[:3, 3] = self.translation
        return M

    @classmethod
    def from_matrix(cls, m: 'np.ndarray') -> 'SE3':
        
        R = SO3.from_matrix(m[:3, :3])
        t = m[:3, 3]
        return cls(R, t)

    def __mul__(self, other: 'SE3') -> 'SE3':
        """Group composition."""
        R1 = self.rotation.as_matrix()
        R2 = other.rotation.as_matrix()
        R = SO3.from_matrix(R1 @ R2)
        t = self.translation + R1 @ other.translation
        return SE3(R, t)

    def inverse(self) -> 'SE3':
        """Return the inverse transformation."""
        R_inv = self.rotation.as_matrix().T
        R = SO3.from_matrix(R_inv)
        t = -(R_inv @ self.translation)
        return SE3(R, t)


def adjoint_se2(g: SE2) -> 'np.ndarray':
    """Return the adjoint matrix of an SE2 element."""
    R = g.rotation.as_matrix()
    x, y = g.translation
    adj = np.eye(3)
    adj[:2, :2] = R
    adj[0, 2] = -y
    adj[1, 2] = x
    return adj


def adjoint_se3(g: SE3) -> 'np.ndarray':
    """Return the adjoint matrix of an SE3 element."""
    R = g.rotation.as_matrix()
    t = g.translation
    adj = np.eye(6)
    adj[:3, :3] = R
    adj[3:, 3:] = R
    adj[:3, 3:] = _skew(t) @ R
    return adj


__all__ = [
    'Quaternion',
    'SO2',
    'SO3',
    'SE2',
    'SE3',
    'adjoint_se2',
    'adjoint_se3',
]
