from agents.news_agent.location_resolver import normalize_location_name

def test_dyurso_maps_to_novorossiysk():
    assert normalize_location_name("Dyurso, Novorossiysk") == "Novorossiysk"

def test_utrish_variants_map_to_same_location():
    assert normalize_location_name("Utrish Nature Reserve") == "Utrish Reserve"
    assert normalize_location_name("Большой Утриш") == "Utrish Reserve"

def test_unknown_location_is_preserved():
    assert normalize_location_name("Unknown Place") == "Unknown Place"
