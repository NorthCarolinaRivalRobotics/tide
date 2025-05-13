"""
Tests for the robot configuration models.
"""
import pytest
from hypothesis import given, strategies as st

from tide.models.robot import (
    RobotType,
    SensorType,
    SensorConfig,
    ActuatorConfig,
    RobotConfig,
    FleetConfig
)


class TestRobotModels:
    """Tests for robot configuration models."""
    
    def test_robot_type(self):
        """Test RobotType enum."""
        assert RobotType.DIFFERENTIAL == "differential"
        assert RobotType.ACKERMANN == "ackermann"
        assert RobotType.OMNI == "omnidirectional"
        assert RobotType.MANIPULATOR == "manipulator"
        
        # Test type comparison
        robot_type = RobotType.DIFFERENTIAL
        assert robot_type == "differential"
        assert robot_type != "ackermann"
    
    def test_sensor_type(self):
        """Test SensorType enum."""
        assert SensorType.LIDAR == "lidar"
        assert SensorType.CAMERA == "camera"
        assert SensorType.IMU == "imu"
        assert SensorType.GPS == "gps"
        assert SensorType.ENCODER == "encoder"
        
        # Test type comparison
        sensor_type = SensorType.LIDAR
        assert sensor_type == "lidar"
        assert sensor_type != "camera"
    
    def test_sensor_config(self):
        """Test SensorConfig model."""
        # Create a sensor config
        sensor = SensorConfig(
            type=SensorType.LIDAR,
            name="front_lidar",
            topic="/robot/lidar/front",
            port="/dev/ttyUSB0",
            parameters={"rpm": 600, "fov": 270.0}
        )
        
        # Check fields
        assert sensor.type == SensorType.LIDAR
        assert sensor.name == "front_lidar"
        assert sensor.topic == "/robot/lidar/front"
        assert sensor.port == "/dev/ttyUSB0"
        assert sensor.parameters["rpm"] == 600
        assert sensor.parameters["fov"] == 270.0
        
        # Test with missing optional fields
        sensor = SensorConfig(
            type=SensorType.CAMERA,
            name="rgb_camera",
            topic="/robot/camera/rgb"
        )
        
        assert sensor.type == SensorType.CAMERA
        assert sensor.name == "rgb_camera"
        assert sensor.topic == "/robot/camera/rgb"
        assert sensor.port is None
        assert sensor.parameters == {}
    
    def test_actuator_config(self):
        """Test ActuatorConfig model."""
        # Create an actuator config
        actuator = ActuatorConfig(
            type="servo",
            name="arm_joint_1",
            topic="/robot/arm/joint1",
            port="/dev/ttyACM0",
            parameters={"min_angle": -90.0, "max_angle": 90.0}
        )
        
        # Check fields
        assert actuator.type == "servo"
        assert actuator.name == "arm_joint_1"
        assert actuator.topic == "/robot/arm/joint1"
        assert actuator.port == "/dev/ttyACM0"
        assert actuator.parameters["min_angle"] == -90.0
        assert actuator.parameters["max_angle"] == 90.0
        
        # Test with missing optional fields
        actuator = ActuatorConfig(
            type="motor",
            name="left_wheel",
            topic="/robot/wheels/left"
        )
        
        assert actuator.type == "motor"
        assert actuator.name == "left_wheel"
        assert actuator.topic == "/robot/wheels/left"
        assert actuator.port is None
        assert actuator.parameters == {}
    
    def test_robot_config(self):
        """Test RobotConfig model."""
        # Create sensors and actuators
        lidar = SensorConfig(
            type=SensorType.LIDAR,
            name="lidar",
            topic="/robot/lidar"
        )
        
        imu = SensorConfig(
            type=SensorType.IMU,
            name="imu",
            topic="/robot/imu"
        )
        
        left_wheel = ActuatorConfig(
            type="motor",
            name="left_wheel",
            topic="/robot/motor/left"
        )
        
        right_wheel = ActuatorConfig(
            type="motor",
            name="right_wheel",
            topic="/robot/motor/right"
        )
        
        # Create the robot config
        robot = RobotConfig(
            name="turtlebot",
            type=RobotType.DIFFERENTIAL,
            description="TurtleBot 3 Burger",
            sensors=[lidar, imu],
            actuators=[left_wheel, right_wheel],
            parameters={"max_speed": 0.22, "max_angular_speed": 2.84}
        )
        
        # Check fields
        assert robot.name == "turtlebot"
        assert robot.type == RobotType.DIFFERENTIAL
        assert robot.description == "TurtleBot 3 Burger"
        assert len(robot.sensors) == 2
        assert len(robot.actuators) == 2
        assert robot.parameters["max_speed"] == 0.22
        assert robot.parameters["max_angular_speed"] == 2.84
        
        # Test that instances were properly added
        assert robot.sensors[0].name == "lidar"
        assert robot.sensors[1].name == "imu"
        assert robot.actuators[0].name == "left_wheel"
        assert robot.actuators[1].name == "right_wheel"
    
    def test_fleet_config(self):
        """Test FleetConfig model."""
        # Create a simple robot
        robot1 = RobotConfig(
            name="robot1",
            type=RobotType.DIFFERENTIAL,
            sensors=[
                SensorConfig(type=SensorType.LIDAR, name="lidar", topic="/robot1/lidar")
            ]
        )
        
        robot2 = RobotConfig(
            name="robot2",
            type=RobotType.ACKERMANN,
            sensors=[
                SensorConfig(type=SensorType.LIDAR, name="lidar", topic="/robot2/lidar")
            ]
        )
        
        # Create the fleet
        fleet = FleetConfig(
            name="test_fleet",
            robots=[robot1, robot2],
            parameters={"formation": "line", "spacing": 2.0}
        )
        
        # Check fields
        assert fleet.name == "test_fleet"
        assert len(fleet.robots) == 2
        assert fleet.parameters["formation"] == "line"
        assert fleet.parameters["spacing"] == 2.0
        
        # Test that robots were properly added
        assert fleet.robots[0].name == "robot1"
        assert fleet.robots[1].name == "robot2"
        assert fleet.robots[0].type == RobotType.DIFFERENTIAL
        assert fleet.robots[1].type == RobotType.ACKERMANN
    
    # Property-based tests
    @given(
        name=st.text(min_size=1, max_size=30),
        topic=st.text(min_size=1, max_size=50),
        sensor_type=st.sampled_from(list(SensorType))
    )
    def test_sensor_config_properties(self, name, topic, sensor_type):
        """Property-based test for SensorConfig."""
        # Create a sensor with the given properties
        sensor = SensorConfig(
            type=sensor_type,
            name=name,
            topic=topic
        )
        
        # Check that the properties were set correctly
        assert sensor.type == sensor_type
        assert sensor.name == name
        assert sensor.topic == topic
    
    @given(
        name=st.text(min_size=1, max_size=30),
        robot_type=st.sampled_from(list(RobotType)),
        max_speed=st.floats(min_value=0.1, max_value=10.0)
    )
    def test_robot_config_properties(self, name, robot_type, max_speed):
        """Property-based test for RobotConfig."""
        # Create a robot with the given properties
        robot = RobotConfig(
            name=name,
            type=robot_type,
            parameters={"max_speed": max_speed}
        )
        
        # Check that the properties were set correctly
        assert robot.name == name
        assert robot.type == robot_type
        assert robot.parameters["max_speed"] == max_speed 