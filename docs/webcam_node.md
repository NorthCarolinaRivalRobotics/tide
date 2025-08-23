# WebcamNode

`WebcamNode` captures frames from a local V4L2 webcam using OpenCV and publishes
raw BGR images on a configurable topic.

## Configuration

Example snippet in `config.yaml`:

```yaml
nodes:
  - type: tide.components.WebcamNode
    params:
      robot_id: robot1
      camera_id: 0            # or path like /dev/video0
      width: 640              # optional
      height: 480             # optional
      output_topic: /robot1/sensor/camera0
      hz: 30.0
      crop_stereo_to_monocular: false  # optional
      crop_to_left: true               # optional (only used when cropping)
```

If `output_topic` is not provided it defaults to
`sensor/camera/{camera_id}/rgb` within the sensor group.
`camera_id` may be an integer index or a device path.

If ``crop_stereo_to_monocular`` is set to ``true``, the node crops each frame
to a single monocular image by taking half the width. ``crop_to_left`` controls
which half is selected (left by default). Both options are typically unused
unless working with stereo cameras that present a combined frame.
