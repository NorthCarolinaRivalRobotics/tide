import argparse
from types import SimpleNamespace
from unittest import mock

import pytest

from tide.cli.main import create_parser
from tide.cli.commands.init import cmd_init
from tide.cli.commands.status import cmd_status
from tide.cli.commands.up import cmd_up


def test_parser_parses_init():
    parser = create_parser()
    args = parser.parse_args(['init', 'proj', '--robot-id', 'r2'])
    assert args.command == 'init'
    assert args.project_name == 'proj'
    assert args.robot_id == 'r2'


def test_parser_rejects_removed_commands():
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['init-config'])
    with pytest.raises(SystemExit):
        parser.parse_args(['init-pingpong'])




def test_cmd_init_creates_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(project_name='proj', robot_id='r1', force=False)
    result = cmd_init(args)
    assert result == 0
    proj_dir = tmp_path / 'proj'
    assert (proj_dir / 'ping_node.py').exists()
    assert (proj_dir / 'pong_node.py').exists()
    assert (proj_dir / 'config' / 'config.yaml').exists()


def test_cmd_status(monkeypatch, capsys):
    monkeypatch.setattr('tide.cli.commands.status.discover_nodes', lambda timeout: [{'robot_id': 'r', 'group': 'g', 'topic': 't'}])
    args = argparse.Namespace(timeout=0.1)
    result = cmd_status(args)
    assert result == 0
    captured = capsys.readouterr()
    assert 'r' in captured.out


def test_cmd_up(monkeypatch, tmp_path):
    cfg_file = tmp_path / 'config.yaml'
    cfg_file.write_text('session:\n  mode: peer\nnodes: []\n')
    args = argparse.Namespace(config=str(cfg_file))

    dummy_node = SimpleNamespace(threads=[object()], stop=mock.Mock())
    monkeypatch.setattr('tide.cli.commands.up.launch_from_config', lambda cfg: [dummy_node])
    with pytest.raises(SystemExit):
        cmd_up(args, run_duration=0.1)
    dummy_node.stop.assert_called()


def test_discover_nodes_parses_keys(monkeypatch):
    class FakeKeyExpr:
        def __init__(self, key):
            self._key = key
        def to_string(self):
            return self._key
    class FakeReply:
        def __init__(self, key):
            self.ok = SimpleNamespace(key_expr=FakeKeyExpr(key))
    class FakeSession:
        def get(self, expr):
            return [FakeReply('robotA/ping/ping')]
        def close(self):
            pass

    monkeypatch.setattr('tide.cli.utils.zenoh.open', lambda cfg=None: FakeSession())

    from importlib import reload
    import tide.cli.utils as utils
    reload(utils)

    nodes = utils.discover_nodes(timeout=0.1)
    assert len(nodes) == 1
    assert nodes[0]['robot_id'] == 'robotA'
    assert nodes[0]['group'] == 'ping'
    assert nodes[0]['topic'] == 'ping'
