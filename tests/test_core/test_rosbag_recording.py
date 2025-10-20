from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import yaml

from tide.cli.commands.up import cmd_up


def _run_cmd_up(config_path, monkeypatch, *, run_duration: float, **env) -> None:
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, str(value))
    args = SimpleNamespace(config=str(config_path))
    with pytest.raises(SystemExit):
        cmd_up(args, run_duration=run_duration)


def test_rosbag_record_and_playback(tmp_path, monkeypatch):
    record_log = tmp_path / "record_log.json"
    playback_log = tmp_path / "playback_log.json"
    bag_dir = tmp_path / "rosbag"

    record_config = {
        "session": {"mode": "peer"},
        "nodes": [
            {
                "type": "tests.test_support.rosbag_nodes.PublisherNode",
                "params": {
                    "robot_id": "testbot",
                    "topic": "test/counter",
                    "max_count": 8,
                },
            },
            {
                "type": "tests.test_support.rosbag_nodes.FileCollectorNode",
                "params": {
                    "robot_id": "testbot",
                    "topic": "test/counter",
                    "log_path": str(record_log),
                },
            },
        ],
    }

    record_config_path = tmp_path / "record_config.yaml"
    record_config_path.write_text(yaml.safe_dump(record_config))

    _run_cmd_up(
        record_config_path,
        monkeypatch,
        run_duration=1.5,
        TIDE_RECORD_BAG=bag_dir,
        TIDE_PLAYBACK_BAG=None,
    )

    assert bag_dir.exists()
    assert (bag_dir / "metadata.yaml").exists()

    record_data = json.loads(record_log.read_text())
    counts = [entry["count"] for entry in record_data]
    assert len(counts) >= 3, "publisher should have produced several messages"

    playback_config = {
        "session": {"mode": "peer"},
        "nodes": [
            {
                "type": "tests.test_support.rosbag_nodes.FileCollectorNode",
                "params": {
                    "robot_id": "testbot",
                    "topic": "test/counter",
                    "log_path": str(playback_log),
                },
            }
        ],
    }

    playback_config_path = tmp_path / "playback_config.yaml"
    playback_config_path.write_text(yaml.safe_dump(playback_config))

    _run_cmd_up(
        playback_config_path,
        monkeypatch,
        run_duration=4.0,
        TIDE_RECORD_BAG=None,
        TIDE_PLAYBACK_BAG=bag_dir,
    )

    playback_data = json.loads(playback_log.read_text())
    assert playback_data == record_data
