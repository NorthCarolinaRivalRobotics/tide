from enum import Enum
from typing import Dict, List, Optional, Union

try:
    from pydantic import BaseModel, Field
except ImportError:
    print("Pydantic not installed. Please install it with 'pip install pydantic'")
    # Provide fallbacks to allow import to continue
    BaseModel = object
    Field = lambda *args, **kwargs: None  # noqa


class RobotType(str, Enum):
    """Types of supported robots."""
    DIFFERENTIAL = "differential"
    ACKERMANN = "ackermann"
    OMNI = "omnidirectional"
    MANIPULATOR = "manipulator"


class SensorType(str, Enum):
    """Types of supported sensors."""
    LIDAR = "lidar"
    CAMERA = "camera"
    IMU = "imu"
    GPS = "gps"
    ENCODER = "encoder"


class SensorConfig(BaseModel):
    """Configuration for a robot sensor."""
    type: SensorType
    name: str
    topic: str
    port: Optional[str] = None
    parameters: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)


class ActuatorConfig(BaseModel):
    """Configuration for a robot actuator."""
    type: str
    name: str
    topic: str
    port: Optional[str] = None
    parameters: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)


class RobotConfig(BaseModel):
    """Configuration for a robot."""
    name: str
    type: RobotType
    description: Optional[str] = None
    sensors: List[SensorConfig] = Field(default_factory=list)
    actuators: List[ActuatorConfig] = Field(default_factory=list)
    parameters: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)


class FleetConfig(BaseModel):
    """Configuration for a fleet of robots."""
    name: str
    robots: List[RobotConfig] = Field(default_factory=list)
    parameters: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict) 