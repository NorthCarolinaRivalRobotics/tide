import numpy as np
import rerun as rr

from tide.components.rerun_node import (
    RerunNode,
    _LOGGERS,
    _log_pose2d,
    _log_pose3d,
    _log_twist2d,
    _log_twist3d,
    _log_accel3d,
    _log_image,
    _log_laserscan,
    _log_occupancy,
    _log_motor_position,
    _log_motor_velocity,
)
from tide.models.common import (
    Acceleration3D,
    Image,
    LaserScan,
    MotorPosition,
    MotorVelocity,
    OccupancyGrid2D,
    Pose2D,
    Pose3D,
    Twist2D,
    Twist3D,
)


rr.init("test_rerun_node", spawn=False)


def test_guess_type():
    node = RerunNode(config={"topics": []})
    assert node._guess_type("camera") is Image
    assert node._guess_type("pose") is Pose2D
    assert node._guess_type("pose3") is Pose3D
    assert node._guess_type("twist") is Twist2D
    assert node._guess_type("twist3") is Twist3D
    assert node._guess_type("accel") is Acceleration3D
    assert node._guess_type("scan") is LaserScan
    assert node._guess_type("grid") is OccupancyGrid2D
    assert node._guess_type("motor/velocity") is MotorVelocity
    assert node._guess_type("motor/position") is MotorPosition


def test_logging_functions():
    _log_pose2d("pose2d", Pose2D(x=1, y=2, theta=0.1))
    _log_pose3d("pose3d", Pose3D())
    _log_twist2d("twist2d", Twist2D())
    _log_twist3d("twist3d", Twist3D())
    _log_accel3d("accel", Acceleration3D())

    img = Image(height=1, width=1, encoding="mono8", step=1, data=b"\x00")
    _log_image("image", img)

    scan = LaserScan(
        angle_min=0.0,
        angle_max=1.0,
        angle_increment=1.0,
        time_increment=0.0,
        scan_time=0.0,
        range_min=0.0,
        range_max=1.0,
        ranges=[1.0, 1.0],
    )
    _log_laserscan("scan", scan)

    grid = OccupancyGrid2D(width=1, height=1, resolution=1.0, data=[0])
    _log_occupancy("grid", grid)

    _log_motor_position("motor/pos", MotorPosition(rotations=1.0))
    _log_motor_velocity("motor/vel", MotorVelocity(rotations_per_sec=2.0))

    # ensure mapping covers all entries
    for typ in [
        Pose2D,
        Pose3D,
        Twist2D,
        Twist3D,
        Acceleration3D,
        Image,
        LaserScan,
        OccupancyGrid2D,
        MotorPosition,
        MotorVelocity,
    ]:
        assert typ in _LOGGERS
