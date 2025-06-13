# PIDNode

`PIDNode` implements a simple proportional–integral–derivative controller.  It reads a state value and a reference value from configurable topics and publishes a command value.

## Configuration

Example snippet in `config.yaml`:

```yaml
nodes:
  - type: tide.components.PIDNode
    params:
      robot_id: robot1
      k_p: 1.2
      k_i: 0.0
      k_d: 0.0
      state_topic: /robot1/state/x
      reference_topic: /robot1/ref/x
      command_topic: /robot1/cmd/x
      hz: 50.0
```

`state_topic`, `reference_topic` and `command_topic` may be absolute topic names (starting with `/`) or relative to the node's group.
