# Tide Configuration Specification

Tide projects are configured using a YAML file describing the Zenoh session and the nodes to launch.

## Top-Level Structure

```yaml
session:
  mode: peer
nodes:
  - type: mypackage.MyNode
    name: optional-name
    params:
      robot_id: myrobot
```

### `session`

- **mode**: Either `peer` or `client`. Defaults to `peer` if omitted.

### `nodes`

A list of node definitions. Each item accepts the following fields:

- **type** (str, required): Python import path to the node class.
- **name** (str, optional): Human friendly identifier.
- **params** (mapping, optional): Parameters passed to the node constructor.

Any unknown keys will raise a validation error when the configuration is loaded.

Use `tide.config.load_config()` to read and validate a configuration file. The function returns a `TideConfig` instance which can be passed to `tide.core.utils.launch_from_config()`.
