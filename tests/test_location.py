"""Geocoding is opt-in and never guesses a timezone or birth time."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "location.py"


def test_city_lookup_refuses_network_without_explicit_permission(tmp_path):
    query = tmp_path / "city.txt"
    query.write_text("长春，中国", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "--query-file", str(query)],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 2, result.stderr
    payload = json.loads(result.stdout)
    assert payload["network_used"] is False
    assert payload["error_type"] == "network_permission_required"
    assert payload["timezone"] is None
    assert payload["candidates"] == []


def test_city_candidate_mapping_uses_actual_upstream_coordinates_without_timezone():
    import importlib.util
    spec = importlib.util.spec_from_file_location("lilith_location", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Synthetic upstream HTTP fixture, not fabricated live lookup evidence.
    rows = [{"display_name": "合成城市甲", "lat": "43.8", "lon": "125.3", "osm_type": "relation", "osm_id": 123}]
    assert hasattr(module, "parse_candidates"), "Missing upstream response parser"
    result = module.parse_candidates(rows)
    assert result == [{"name": "合成城市甲", "latitude": 43.8, "longitude": 125.3,
                       "osm_type": "relation", "osm_id": 123, "timezone": None}]


def test_network_lookup_uses_fixed_endpoint_city_only_and_bounded_response(tmp_path, monkeypatch, capsys):
    import importlib.util
    spec = importlib.util.spec_from_file_location("lilith_location_network", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    query = tmp_path / "city.txt"
    query.write_text("合成城市甲，中国", encoding="utf-8")
    calls = []

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
        def read(self, maximum):
            assert maximum <= 1024 * 1024 + 1
            return json.dumps([{"display_name": "合成城市甲", "lat": "43.8", "lon": "125.3"}]).encode()

    def upstream(request, timeout):
        assert request.full_url.startswith("https://nominatim.openstreetmap.org/search?")
        assert "limit=3" in request.full_url
        assert 0 < timeout <= 20
        calls.append(request)
        return Response()

    monkeypatch.setattr(module, "urlopen", upstream)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--query-file", str(query), "--allow-network"])
    assert module.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(calls) == 1
    assert payload["network_used"] is True
    assert payload["success"] is True
    assert payload["timezone"] is None
    assert payload["candidates"][0]["latitude"] == 43.8


def test_parse_invalid_coordinates_fails_cleanly():
    import importlib.util
    import pytest
    spec = importlib.util.spec_from_file_location("lilith_location_bad", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for rows in [[{"display_name": "x", "lat": "nan", "lon": "1"}], {}, [{}], [{"display_name": "x", "lat": None, "lon": "1"}]]:
        with pytest.raises(ValueError):
            module.parse_candidates(rows)


def test_candidate_names_reject_unpaired_surrogates():
    import importlib.util
    import pytest
    spec = importlib.util.spec_from_file_location("lilith_location_unicode", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError):
        module.parse_candidates([{"display_name": chr(0xD800), "lat": "1", "lon": "1"}])


def test_boolean_coordinates_are_not_numbers():
    import importlib.util
    import pytest
    spec = importlib.util.spec_from_file_location("lilith_location_bool", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for coordinate in [True, False]:
        with pytest.raises(ValueError):
            module.parse_candidates([{"display_name": "synthetic", "lat": coordinate, "lon": "1"}])
