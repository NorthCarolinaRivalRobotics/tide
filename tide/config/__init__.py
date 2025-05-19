from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

import yaml
from enum import Enum
from pydantic import BaseModel, Field


class SessionMode(str, Enum):
    peer = "peer"
    client = "client"


class SessionConfig(BaseModel):
    """Configuration for the Zenoh session."""

    mode: SessionMode = Field(default=SessionMode.peer, description="Zenoh session mode")


class NodeConfig(BaseModel):
    """Configuration for a single Tide node."""

    type: str
    name: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class TideConfig(BaseModel):
    """Top level configuration model."""

    session: SessionConfig = Field(default_factory=SessionConfig)
    nodes: List[NodeConfig] = Field(default_factory=list)


def load_config(source: Union[str, Path, Mapping[str, Any]]) -> TideConfig:
    """Load and validate a configuration from YAML or a mapping."""

    if isinstance(source, (str, Path)):
        with open(source, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = dict(source)
    return TideConfig.model_validate(data)


__all__ = [
    "SessionMode",
    "SessionConfig",
    "NodeConfig",
    "TideConfig",
    "load_config",
]
