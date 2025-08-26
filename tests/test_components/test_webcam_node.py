import os
import time
import pytest
import numpy as np

from tide.core.node import BaseNode
from tide.core.utils import launch_from_config
from tide.config import TideConfig, NodeConfig
from tide.models.common import Image
from tide.components.webcam_node import WebcamNode

import cv2


CAM = os.getenv("TEST_CAMERA", "/dev/video0")


class ImageRecorder(BaseNode):
    """Node that records incoming image messages."""

    GROUP = "sink"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = self.config or {}
        self.topic = cfg.get("topic", "camera")
        self.received = []
        self.subscribe(self.topic, self._on_image)

    def _on_image(self, data):
        try:
            self.received.append(Image.model_validate(data))
        except Exception:
            self.received.append(data)

    def step(self):
        pass


@pytest.mark.skipif(not os.path.exists(CAM), reason="no V4L2 device in CI")
def test_webcam_node_integration():
    cfg = TideConfig(
        nodes=[
            NodeConfig(
                type="tide.components.WebcamNode",
                params={
                    "robot_id": "robot",
                    "camera_id": CAM,
                    "width": 320,
                    "height": 240,
                    "output_topic": "/robot/camera0",
                    "hz": 5.0,
                },
            ),
            NodeConfig(
                type="tests.test_components.test_webcam_node.ImageRecorder",
                params={"robot_id": "robot", "topic": "/robot/camera0"},
            ),
        ]
    )

    nodes = launch_from_config(cfg)

    # Allow some time for the camera to produce a frame
    time.sleep(1.0)

    for n in nodes:
        n.stop()
    for n in nodes:
        for t in n.threads:
            t.join(timeout=1.0)

    recorder = nodes[-1]
    assert getattr(recorder, "received", None), "no frame received"
    img = recorder.received[0]
    assert isinstance(img, Image)
    assert img.width > 0 and img.height > 0 and img.data


def test_crop_stereo_to_monocular():
    """Ensure frames are cropped when requested."""

    class FakeCap:
        def __init__(self, frame):
            self._frame = frame

        def isOpened(self):
            return True

        def read(self):
            return True, self._frame

    # Create a frame with distinct halves for verification
    frame = np.zeros((10, 20, 3), dtype=np.uint8)
    frame[:, :10, 0] = 1  # left half
    frame[:, 10:, 0] = 2  # right half

    node = WebcamNode(config={"crop_stereo_to_monocular": True})
    node.cap = FakeCap(frame)
    published: list[Image] = []
    node.put = lambda topic, msg: published.append(msg)
    node.step()

    assert published, "no image published"
    img = published[0]
    assert img.width == 10 and img.height == 10
    arr = np.frombuffer(img.data, dtype=np.uint8).reshape(img.height, img.width, 3)
    assert np.all(arr[:, :, 0] == 1)

    # Right half cropping
    node = WebcamNode(
        config={"crop_stereo_to_monocular": True, "crop_to_left": False}
    )
    node.cap = FakeCap(frame)
    published = []
    node.put = lambda topic, msg: published.append(msg)
    node.step()

    img = published[0]
    arr = np.frombuffer(img.data, dtype=np.uint8).reshape(img.height, img.width, 3)
    assert np.all(arr[:, :, 0] == 2)
