import json

from config import normalize_port, write_api_port_runtime


def test_api_port_defaults_and_bounds():
    assert normalize_port(None) == 8766
    assert normalize_port("not-a-port") == 8766
    assert normalize_port(0) == 8766
    assert normalize_port(65536) == 8766
    assert normalize_port("9876") == 9876


def test_runtime_api_port_file_contains_only_custom_port(tmp_path):
    runtime_path = write_api_port_runtime(tmp_path, 9876)

    assert runtime_path.name == "_preset-api.json"
    assert json.loads(runtime_path.read_text(encoding="utf-8")) == {"apiPort": 9876}
