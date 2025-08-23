import time

from tide.core.node import BaseNode
from tide.models.common import Image
from tide.namespaces import sensor_camera_rgb


class WebcamNode(BaseNode):
    """Node that captures frames from a webcam using OpenCV.

    Parameters in ``config``:

    - ``camera_id``: integer or device path for the webcam (default: 0)
    - ``width``/``height`` or ``resolution``: optional capture resolution
    - ``output_topic``: topic to publish :class:`~tide.models.common.Image`
    - ``hz``: publishing rate
    - ``crop_stereo_to_monocular``: if true, crop a stereo pair to a single
      image by taking half of the frame (default: false)
    - ``crop_to_left``: when cropping, choose the left half if true or the
      right half if false (default: true)
    """

    GROUP = "sensor"

    def __init__(self, *, config: dict | None = None) -> None:
        super().__init__(config=config)
        cfg = config or {}

        self.camera_id = cfg.get("camera_id", 0)
        # Resolution can be specified as [width, height] or separate keys
        if "resolution" in cfg:
            self.width, self.height = cfg["resolution"]
        else:
            self.width = cfg.get("width")
            self.height = cfg.get("height")

        self.output_topic = cfg.get("output_topic") or sensor_camera_rgb(str(self.camera_id))


        self.hz = float(cfg.get("hz", self.hz))

        # Optional stereo cropping parameters
        self.crop_stereo_to_monocular = bool(
            cfg.get("crop_stereo_to_monocular", False)
        )
        # Defaults to True when cropping is enabled
        self.crop_to_left = bool(cfg.get("crop_to_left", True))

        try:
            import cv2

            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_V4L2)
            if self.width:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.width))
            if self.height:
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.height))
        except Exception as e:
            print(f"Error initializing OpenCV: {e}")
            self.cap = None

    def step(self) -> None:
        if not self.cap or not self.cap.isOpened():
            return

        ok, frame = self.cap.read()
        for _ in range(10):
            if ok and frame is not None and frame.size:
                break
            time.sleep(0.01)
            ok, frame = self.cap.read()

        if not ok or frame is None or frame.size == 0:
            return

        if self.crop_stereo_to_monocular:
            half = frame.shape[1] // 2
            frame = frame[:, :half] if self.crop_to_left else frame[:, half:]
        height, width, channels = frame.shape
        img = Image(
            height=height,
            width=width,
            encoding="bgr8",
            step=width * channels,
            data=frame.tobytes(),
        )
        self.put(self.output_topic, img)

    def stop(self) -> None:
        try:
            if self.cap and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
        super().stop()
