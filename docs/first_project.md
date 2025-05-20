# Your First Tide Project

This guide walks you through creating a simple Tide project and running it with mock hardware. It assumes you have already cloned the repository and installed its dependencies.

## Install Dependencies

Run the provided script from the project root:

```bash
chmod +x install-deps.bash
./install-deps.bash
```

This installs `uv` and synchronizes all Python packages.

## Create a Project

Use the Tide CLI to generate a new project skeleton. Choose a project name and robot id:

```bash
tide init my_first_robot --robot-id mockbot
cd my_first_robot
```

The command creates a directory containing a `config/` folder and example nodes in `nodes/`.

## Configure Mock Hardware

For quick testing you can simulate sensors and actuators. Create a new node in `nodes/mock_driver.py`:

```python
from tide.core.node import BaseNode
from tide import CmdTopic, StateTopic
from tide.models import Twist2D, Pose2D
from tide.models.serialization import to_zenoh_value

class MockDriver(BaseNode):
    """Simulates a simple mobile robot."""
    ROBOT_ID = "mockbot"
    GROUP = "mock"

    def __init__(self, *, config=None):
        super().__init__(config=config)
        self.pose = Pose2D(x=0.0, y=0.0, theta=0.0)
        self.subscribe(CmdTopic.TWIST.value, self.on_cmd_vel)

    def on_cmd_vel(self, sample):
        twist = Twist2D.parse_raw(sample.payload)
        self.pose.x += twist.linear.x * 0.1
        self.pose.y += twist.linear.y * 0.1

    def step(self):
        self.put(StateTopic.POSE2D.value, to_zenoh_value(self.pose))
```

Add the node to `config/config.yaml`:

```yaml
nodes:
  - type: nodes.mock_driver.MockDriver
    params:
      robot_id: mockbot
```

## Run the Project

Start the nodes defined in the configuration:

```bash
tide up
```

The mock driver publishes state updates while listening for velocity commands. You now have a working Tide setup without physical hardware.


## Add a Command Publisher

Create a second node to drive the mock robot by publishing `cmd/twist` messages. Save this as `nodes/cmd_publisher.py`:

```python
from tide.core.node import BaseNode
from tide import CmdTopic
from tide.models import Twist2D, Vector2
from tide.models.serialization import to_zenoh_value

class CmdPublisher(BaseNode):
    """Sends a constant forward velocity command."""
    ROBOT_ID = "mockbot"
    GROUP = "teleop"
    hz = 2.0

    def step(self):
        cmd = Twist2D(linear=Vector2(x=0.2), angular=0.0)
        self.put(CmdTopic.TWIST.value, to_zenoh_value(cmd))
```

Update `config/config.yaml` to include both nodes:

```yaml
nodes:
  - type: nodes.mock_driver.MockDriver
    params:
      robot_id: mockbot
  - type: nodes.cmd_publisher.CmdPublisher
    params:
      robot_id: mockbot
```

Run `tide up` again and the mock driver will move according to the published commands.
