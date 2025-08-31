from __future__ import annotations

from typing import Any, List, Dict, Type

from tide.core.node import BaseNode

try:
    from pydantic import BaseModel
except Exception:  # pragma: no cover - pydantic is required for typing but optional at runtime
    BaseModel = object  # type: ignore


class MuxNode(BaseNode):
    """Priority-based topic multiplexer.

    This node subscribes to multiple input topics that share the same
    message type and republishes data from the highest-priority topic
    that has produced a new message.

    Lower-priority messages are discarded whenever a higher-priority
    topic provides data in the same iteration.

    Parameters in ``config``:

    - ``inputs``: iterable of ``{"topic": str, "priority": int}``
      mappings. Smaller ``priority`` numbers imply higher priority.
    - ``output_topic``: topic where the selected message will be
      published. Defaults to ``"mux"``.
    - ``msg_type``: optional Pydantic model class or import string used
      to reconstruct messages from dictionaries before publishing. When
      omitted, dictionaries are forwarded as-is.
    """

    GROUP = "mux"

    def __init__(self, *, config: dict | None = None) -> None:
        super().__init__(config=config)
        cfg = config or {}

        inputs = cfg.get("inputs")
        if not inputs:
            raise ValueError("MuxNode requires an 'inputs' list in the config")

        self.output_topic: str = cfg.get("output_topic", "mux")

        self.inputs: List[Dict[str, Any]] = []
        for entry in inputs:
            if isinstance(entry, dict):
                topic = entry.get("topic")
                priority = int(entry.get("priority", 0))
            else:
                # Support simple tuple/list form (topic, priority)
                topic, priority = entry  # type: ignore[misc]
            if topic is None:
                raise ValueError("Each input must specify a topic")
            self.inputs.append({"topic": topic, "priority": priority})
            self.subscribe(topic)

        # Sort once by priority (lower value = higher priority)
        self.inputs.sort(key=lambda x: x["priority"])

        msg_type = cfg.get("msg_type")
        if isinstance(msg_type, str):
            self.msg_type = self._import_string(msg_type)
        else:
            self.msg_type = msg_type

    def _import_string(self, path: str) -> Type[Any]:
        """Import a class from a fully qualified path."""
        module_name, class_name = path.rsplit(".", 1)
        try:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as exc:
            raise ImportError(
                f"Could not import '{path}'. Error: {exc}"
            ) from exc

    def _maybe_convert(self, msg: Any) -> Any:
        if self.msg_type and isinstance(msg, dict) and issubclass(self.msg_type, BaseModel):
            try:
                return self.msg_type.model_validate(msg)
            except Exception:
                pass
        return msg

    def step(self) -> None:
        published = False
        for entry in self.inputs:
            topic = entry["topic"]
            val = self.take(topic)
            if val is not None:
                if not published:
                    self.put(self.output_topic, self._maybe_convert(val))
                    published = True
                # else: higher-priority message already published; discard
        # Nothing to do if no messages were received this cycle
