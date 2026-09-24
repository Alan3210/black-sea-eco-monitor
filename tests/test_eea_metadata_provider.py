from backend.services.eea_metadata_provider import EEAMetadataProvider

def test_provider_init(tmp_path):
    p = EEAMetadataProvider(cache_dir=tmp_path)
    assert p.cache_dir == tmp_path
