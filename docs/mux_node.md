# MuxNode

The `MuxNode` provides a simple priority-based multiplexer for topics of the
same message type.  It subscribes to multiple input topics, each assigned a
priority, and republishes the message from the highest-priority topic that
produces data.

Lower-priority messages are discarded whenever a higher-priority topic has
new data. This is useful for commanding robots from multiple sources, such as
manual teleoperation overriding autonomous navigation commands.

## Configuration

```yaml
nodes:
  - type: tide.components.MuxNode
    params:
      robot_id: robot
      inputs:
        - topic: cmd/teleop
          priority: 0   # Highest priority
        - topic: cmd/autonomy
          priority: 1
      output_topic: cmd/mux
      msg_type: tide.models.common.Twist2D
```

- `inputs` – list of `{topic, priority}` pairs. Smaller numbers have higher
  priority.
- `output_topic` – topic where the selected message is published.
- `msg_type` – (optional) fully qualified name of the Pydantic model used to
  reconstruct messages before publishing.

Only one message is published per iteration: the highest-priority message that
was received since the previous step.
