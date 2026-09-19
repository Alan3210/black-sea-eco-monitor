from backend.services.impact_registry import get_impact_registry_targets

def test_registry_has_25_targets():
    targets = get_impact_registry_targets()
    assert len(targets) == 25
    assert any(t.name == "Utrish Reserve" for t in targets)
