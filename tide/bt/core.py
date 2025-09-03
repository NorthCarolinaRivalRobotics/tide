from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Any


class Status(Enum):
    """Result of a behavior tree node tick."""

    SUCCESS = auto()
    FAILURE = auto()
    RUNNING = auto()


class BTNode:
    """Base class for all behavior tree nodes."""

    def tick(self, blackboard: Dict[str, Any]) -> Status:
        """Execute one cycle of the node.

        Args:
            blackboard: Mutable dictionary for sharing state between nodes.

        Returns:
            Status of this node after the tick.
        """

        raise NotImplementedError


class Action(BTNode):
    """Leaf node that executes a callable."""

    def __init__(self, func: Callable[[Dict[str, Any]], Status | bool]) -> None:
        self.func = func

    def tick(self, blackboard: Dict[str, Any]) -> Status:  # pragma: no cover - docstring only
        result = self.func(blackboard)
        if isinstance(result, Status):
            return result
        return Status.SUCCESS if result else Status.FAILURE


class Condition(BTNode):
    """Leaf node that evaluates a boolean predicate."""

    def __init__(self, predicate: Callable[[Dict[str, Any]], bool]) -> None:
        self.predicate = predicate

    def tick(self, blackboard: Dict[str, Any]) -> Status:  # pragma: no cover - docstring only
        return Status.SUCCESS if self.predicate(blackboard) else Status.FAILURE


class Sequence(BTNode):
    """Run children in order until one fails."""

    def __init__(self, children: List[BTNode]) -> None:
        self.children = list(children)
        self._index = 0

    def tick(self, blackboard: Dict[str, Any]) -> Status:
        while self._index < len(self.children):
            status = self.children[self._index].tick(blackboard)
            if status == Status.RUNNING:
                return Status.RUNNING
            if status == Status.FAILURE:
                self._index = 0
                return Status.FAILURE
            self._index += 1
        self._index = 0
        return Status.SUCCESS


class Selector(BTNode):
    """Run children until one succeeds."""

    def __init__(self, children: List[BTNode]) -> None:
        self.children = list(children)
        self._index = 0

    def tick(self, blackboard: Dict[str, Any]) -> Status:
        while self._index < len(self.children):
            status = self.children[self._index].tick(blackboard)
            if status == Status.RUNNING:
                return Status.RUNNING
            if status == Status.SUCCESS:
                self._index = 0
                return Status.SUCCESS
            self._index += 1
        self._index = 0
        return Status.FAILURE


class BehaviorTree:
    """Container that ticks a root node."""

    def __init__(self, root: BTNode, blackboard: Optional[Dict[str, Any]] = None) -> None:
        self.root = root
        self.blackboard: Dict[str, Any] = blackboard if blackboard is not None else {}

    def tick(self) -> Status:
        """Tick the root node of the tree."""

        return self.root.tick(self.blackboard)
