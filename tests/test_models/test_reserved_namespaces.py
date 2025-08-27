import time
from datetime import datetime

import zenoh

from tide.namespaces import (
    CmdTopic,
    StateTopic,
    SensorTopic,
    sensor_camera_rgb,
    sensor_camera_depth,
    motor_cmd_pos,
    motor_cmd_vel,
    motor_pos,
    motor_vel,
    robot_topic,
)
from tide.models import (
    Vector2,
    Vector3,
    Quaternion,
    Twist2D,
    Pose2D,
    Pose3D,
    LaserScan,
    Image,
    MotorPosition,
    MotorVelocity,
)
from tide.models.serialization import to_zenoh_value, from_zenoh_value


def _roundtrip(session: zenoh.Session, key: str, msg, model_cls):
    samples = []
    sub = session.declare_subscriber(key, lambda s: samples.append(s))
    pub = session.declare_publisher(key)
    pub.put(to_zenoh_value(msg))
    end = time.time() + 0.5
    while not samples and time.time() < end:
        time.sleep(0.05)
    assert samples, f"no sample received for {key}"
    payload = samples[0].payload
    if hasattr(payload, "to_bytes"):
        payload = payload.to_bytes()
    received = from_zenoh_value(payload, model_cls)
    sub.undeclare()
    pub.undeclare()
    return received


def test_reserved_namespace_roundtrip():
    zenoh.init_log_from_env_or("error")
    session = zenoh.open(zenoh.Config())
    try:
        robot = "testbot"
        cases = [
            (
                CmdTopic.TWIST,
                Twist2D(
                    linear=Vector2(x=1.0, y=2.0),
                    angular=0.1,
                    timestamp=datetime(2020, 1, 1),
                ),
            ),
            (
                CmdTopic.POSE2D,
                Pose2D(x=1.0, y=2.0, theta=0.5, timestamp=datetime(2020, 1, 1)),
            ),
            (
                CmdTopic.POSE3D,
                Pose3D(
                    position=Vector3(x=1.0, y=2.0, z=3.0),
                    orientation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
                    timestamp=datetime(2020, 1, 1),
                ),
            ),
            (
                StateTopic.POSE2D,
                Pose2D(x=0.0, y=1.0, theta=2.0, timestamp=datetime(2020, 1, 2)),
            ),
            (
                StateTopic.POSE3D,
                Pose3D(
                    position=Vector3(x=0.0, y=1.0, z=2.0),
                    orientation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
                    timestamp=datetime(2020, 1, 2),
                ),
            ),
            (
                StateTopic.TWIST,
                Twist2D(
                    linear=Vector2(x=0.0, y=0.0),
                    angular=1.0,
                    timestamp=datetime(2020, 1, 2),
                ),
            ),
            (
                SensorTopic.LIDAR_SCAN,
                LaserScan(
                    angle_min=0.0,
                    angle_max=1.0,
                    angle_increment=0.1,
                    time_increment=0.0,
                    scan_time=0.1,
                    range_min=0.0,
                    range_max=5.0,
                    ranges=[1.0, 2.0],
                    intensities=[0.0, 1.0],
                ),
            ),
            (
                SensorTopic.IMU_ACCEL,
                Vector3(x=0.1, y=0.2, z=0.3),
            ),
            (
                SensorTopic.IMU_QUAT,
                Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
            ),
        ]

        for topic, msg in cases:
            key = f"{robot}/{topic.value}"
            received = _roundtrip(session, key, msg, type(msg))
            assert received == msg

        # Camera topics with helper functions
        img = Image(height=1, width=1, encoding="rgb8", step=3, data=b"abc")
        key = f"{robot}/" + sensor_camera_rgb("front")
        received = _roundtrip(session, key, img, Image)
        assert received == img

        img = Image(height=1, width=1, encoding="rgb8", step=3, data=b"def")
        key = f"{robot}/" + sensor_camera_depth("front")
        received = _roundtrip(session, key, img, Image)
        assert received == img

        # Motor topics
        pos_msg = MotorPosition(rotations=1.5)
        vel_msg = MotorVelocity(rotations_per_sec=2.0)
        motor_cases = [
            (motor_cmd_pos, pos_msg, MotorPosition),
            (motor_cmd_vel, vel_msg, MotorVelocity),
            (motor_pos, pos_msg, MotorPosition),
            (motor_vel, vel_msg, MotorVelocity),
        ]
        for builder, msg, model in motor_cases:
            key = f"{robot}/" + builder(1)
            received = _roundtrip(session, key, msg, model)
            assert received == msg
    finally:
        session.close()


def test_robot_topic_builder():
    key = robot_topic("rover", CmdTopic.TWIST.value)
    assert key == "/rover/cmd/twist"

