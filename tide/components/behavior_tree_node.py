from __future__ import annotations

import importlib
from typing import Any, Callable, Dict, Optional

from tide.core.node import BaseNode
from tide.bt import BehaviorTree, BTNode


class BehaviorTreeNode(BaseNode):
    """Node that owns and ticks a behavior tree.

    The tree definition is provided via the ``tree`` configuration parameter.
    It may be either an instance of :class:`BTNode`, a callable returning one,
    or a string import path to such a callable. A shared ``blackboard``
    dictionary can also be supplied via the configuration to expose state
    between leaves and to external observers.
    """

    GROUP = "bt"

    def __init__(self, *, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config=config)
        cfg = config or {}
        tree_spec = cfg.get("tree")
        if tree_spec is None:
            raise ValueError("BehaviorTreeNode requires a 'tree' parameter in config")

        self.blackboard: Dict[str, Any] = cfg.get("blackboard", {})
        self.tree = BehaviorTree(self._resolve_tree(tree_spec), self.blackboard)

    def _resolve_tree(self, tree_spec: Any) -> BTNode:
        """Resolve the tree specification into a BTNode."""

        if isinstance(tree_spec, BTNode):
            return tree_spec

        if isinstance(tree_spec, str):
            module_path, attr = tree_spec.rsplit(".", 1)
            module = importlib.import_module(module_path)
            tree_spec = getattr(module, attr)

        if callable(tree_spec):
            tree_spec = tree_spec()

        if not isinstance(tree_spec, BTNode):
            raise TypeError("tree specification must resolve to a BTNode instance")
        return tree_spec

    def step(self) -> None:
        self.tree.tick()
