# BehaviorTreeNode

The `BehaviorTreeNode` ticks a behavior tree each iteration. Behavior trees are
constructed using the utilities in `tide.bt` and are supplied to the node via
the `tree` configuration parameter.

## Configuration

```yaml
nodes:
  - type: tide.components.BehaviorTreeNode
    params:
      robot_id: robot
      tree: my_robot.behaviors.build_tree
      blackboard:
        ready: true
```

- `tree` – Fully qualified import path to a function returning a
  `tide.bt.BTNode` or an instance of one.
- `blackboard` – Optional dictionary shared with the behavior tree. It can be
  used to expose state or parameters to tree nodes or external observers.

## Basic Example

In `my_robot/behaviors.py`:

```python
from tide.bt import Action, Sequence, Status


def build_tree():
    def say_hello(bb):
        print("hello from BT")
        return Status.SUCCESS

    return Sequence([Action(say_hello)])
```

The above function can be referenced in the configuration file so the behavior
runs inside a `BehaviorTreeNode`.

## More Examples

### Drivetrain with Arm Motion

Robots often need to handle a teleoperated drivetrain while occasionally
running an automatic arm sequence. A `Selector` lets the arm sequence preempt
the default teleop drive when a button is pressed.

```python
from tide.bt import Action, Condition, Selector, Sequence, Status


def build_tree():
    def drive_teleop(bb):
        bb["drive"].teleop()
        return Status.SUCCESS

    def arm_auto(bb):
        if bb["arm"].sequence_done():
            return Status.SUCCESS
        bb["arm"].run_sequence()
        return Status.RUNNING

    def arm_requested(bb):
        return bb.get("arm_button", False)

    return Selector([
        Sequence([Condition(arm_requested), Action(arm_auto)]),
        Action(drive_teleop),
    ])
```

The blackboard exposes the drivetrain and arm objects along with the state of a
joystick button. When the arm button is pressed the selector runs the arm
sequence; otherwise normal teleop driving continues.

### Auto Alignment with Teleop Fallback

Another common pattern is to align to a goal pose using odometry and then fall
back to manual control. A `Selector` chooses between alignment logic and
teleoperation based on whether a goal is set.

```python
from tide.bt import Action, Condition, Selector, Sequence, Status


def build_tree():
    def align_to_goal(bb):
        if bb["odometry"].at_goal(bb["goal"]):
            return Status.SUCCESS
        bb["drivetrain"].drive_toward(bb["goal"])
        return Status.RUNNING

    def teleop(bb):
        bb["drivetrain"].teleop()
        return Status.SUCCESS

    def has_goal(bb):
        return bb.get("goal") is not None

    return Selector([
        Sequence([Condition(has_goal), Action(align_to_goal)]),
        Action(teleop),
    ])
```

### Handling Failed Pickups with a Claw Sensor

Sensors can determine whether an action succeeded and trigger recovery
behavior. Here a claw sensor determines whether an object was successfully
grasped. If the sensor does not detect an object the tree retries or aborts the
pickup.

```python
from tide.bt import Action, Condition, Selector, Sequence, Status


def build_tree():
    def attempt_pickup(bb):
        bb["claw"].close()
        return Status.SUCCESS

    def object_detected(bb):
        return bb["claw"].has_object()

    def handle_failure(bb):
        bb["logger"].warning("pickup failed")
        return Status.FAILURE

    return Sequence([
        Action(attempt_pickup),
        Selector([Condition(object_detected), Action(handle_failure)]),
    ])
```

These snippets provide starting points; real robots can share state and
parameters through the blackboard to build rich, predictable behaviors.
