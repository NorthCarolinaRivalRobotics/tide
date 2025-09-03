from tide.bt import Action, BehaviorTree, Condition, Sequence, Selector, Status


def test_sequence_and_selector_flow():
    bb = {"value": 0}

    def inc(bb):
        bb["value"] += 1
        return Status.SUCCESS

    def check(bb):
        return bb["value"] < 2

    tree = BehaviorTree(Sequence([Action(inc), Condition(check)]), bb)
    assert tree.tick() == Status.SUCCESS
    assert bb["value"] == 1
    assert tree.tick() == Status.FAILURE

    bb["value"] = 0
    tree = BehaviorTree(Selector([Condition(check), Action(inc)]), bb)
    assert tree.tick() == Status.SUCCESS
    assert bb["value"] == 0
