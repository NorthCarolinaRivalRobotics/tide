from datetime import datetime
import math
from typing import Dict, List, Optional, Union, Type

try:
    from pydantic import BaseModel, Field, ConfigDict
except ImportError:
    print("Pydantic not installed. Please install it with 'pip install pydantic'")
    # Provide fallbacks to allow import to continue
    BaseModel = object
    Field = lambda *args, **kwargs: None  # noqa
    ConfigDict = dict

class TideMessage(BaseModel):
    """Base class for all messages in the tide framework."""
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict()

    def to_bytes(self) -> bytes:
        """Serialize this message to CBOR bytes."""
        from .serialization import to_cbor

        return to_cbor(self)

    def __bytes__(self) -> bytes:  # type: ignore[override]
        """bytes(obj) returns the CBOR representation."""
        return self.to_bytes()

    @classmethod
    def from_bytes(cls: Type['TideMessage'], data: Union[bytes, str]) -> 'TideMessage':
        """Deserialize bytes into a message instance."""
        from .serialization import from_cbor

        return from_cbor(data, cls)


class Vector2(BaseModel):
    """2D vector representation."""
    x: float = 0.0
    y: float = 0.0


class Vector3(BaseModel):
    """3D vector representation."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Quaternion(BaseModel):
    """Quaternion for 3D orientation."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0  # Default to identity quaternion

    @classmethod
    def from_euler(cls, roll: float, pitch: float, yaw: float) -> "Quaternion":
        """Create a quaternion from roll, pitch, yaw angles."""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        return cls(
            x=cy * cp * sr - sy * sp * cr,
            y=sy * cp * sr + cy * sp * cr,
            z=sy * cp * cr - cy * sp * sr,
            w=cy * cp * cr + sy * sp * sr,
        )

    def to_euler(self) -> tuple[float, float, float]:
        """Convert this quaternion to roll, pitch, yaw angles."""
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


class Header(BaseModel):
    """Common header for messages that need frame information."""
    frame_id: str = ""
    stamp: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict()


class Twist2D(TideMessage):
    """Velocity command in SE(2) - 2D plane with rotation."""
    linear: Vector2 = Field(default_factory=Vector2)
    angular: float = 0.0  # rotation around z-axis


class Twist3D(TideMessage):
    """Velocity command in SE(3) - 3D space with 3D rotation."""
    linear: Vector3 = Field(default_factory=Vector3)
    angular: Vector3 = Field(default_factory=Vector3)


class Pose2D(TideMessage):
    """Position and orientation in SE(2)."""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0  # Orientation in radians


class Pose3D(TideMessage):
    """Position and orientation in SE(3)."""
    position: Vector3 = Field(default_factory=Vector3)
    orientation: Quaternion = Field(default_factory=Quaternion)


class Acceleration3D(TideMessage):
    """Linear and angular acceleration in 3D."""
    linear: Vector3 = Field(default_factory=Vector3)
    angular: Vector3 = Field(default_factory=Vector3)


class OccupancyGrid2D(TideMessage):
    """2D occupancy grid for mapping."""
    header: Header = Field(default_factory=Header)
    width: int
    height: int
    resolution: float  # meters per cell
    origin: Pose2D = Field(default_factory=Pose2D)
    data: List[int]  # 0-100 for free-occupied, -1 for unknown


class LaserScan(TideMessage):
    """2D laser scan data."""
    header: Header = Field(default_factory=Header)
    angle_min: float
    angle_max: float
    angle_increment: float
    time_increment: float
    scan_time: float
    range_min: float
    range_max: float
    ranges: List[float]
    intensities: Optional[List[float]] = None


class Image(TideMessage):
    """Image data."""
    header: Header = Field(default_factory=Header)
    height: int
    width: int
    encoding: str  # rgb8, bgr8, mono8, etc.
    is_bigendian: bool = False
    step: int  # Full row length in bytes
    data: bytes 