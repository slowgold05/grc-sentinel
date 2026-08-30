from ruleset.framework_drift import ControlSnapshot, diff_controls


def test_detects_added_removed_and_materially_changed_controls() -> None:
    old = [
        ControlSnapshot(code="A-1", title="Access", description="Old", params={}),
        ControlSnapshot(code="A-2", title="Review", description="Same", params={}),
        ControlSnapshot(code="A-3", title="Remove", description="Old", params={}),
    ]
    new = [
        ControlSnapshot(code="A-1", title="Access", description="New", params={}),
        ControlSnapshot(code="A-2", title="Review", description="Same", params={}),
        ControlSnapshot(code="A-4", title="Add", description="New", params={}),
    ]
    drift = diff_controls(old, new)
    assert drift.model_dump() == {
        "added": ["A-4"],
        "removed": ["A-3"],
        "changed": ["A-1"],
    }
    assert drift.affected_codes == ["A-1", "A-3", "A-4"]
