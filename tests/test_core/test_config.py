import pytest

from tide.config import load_config, TideConfig, NodeConfig
from tide.core import utils


def test_load_config_from_file(tmp_path):
    cfg_text = """
session:
  mode: peer
nodes:
  - type: example.Node
    params:
      robot_id: r1
"""
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(cfg_text)

    cfg = load_config(cfg_file)
    assert isinstance(cfg, TideConfig)
    assert cfg.session.mode == "peer"
    assert cfg.nodes[0].type == "example.Node"
    assert cfg.nodes[0].params["robot_id"] == "r1"


def test_invalid_mode(tmp_path):
    bad_text = "session:\n  mode: unknown\n"
    path = tmp_path / "bad.yaml"
    path.write_text(bad_text)
    with pytest.raises(Exception):
        load_config(path)


def test_launch_from_config_with_model(monkeypatch):
    cfg = TideConfig(nodes=[NodeConfig(type="d.Node", params={})])

    created = []

    class Dummy:
        def __init__(self, config=None):
            self.config = config
        def start(self):
            created.append(self)
            return None

    monkeypatch.setattr(utils, "create_node", lambda t, p: Dummy(p))

    nodes = utils.launch_from_config(cfg)
    assert len(nodes) == 1
    assert created[0].config == {}
