import importlib.util
from pathlib import Path
import sys
import types

import pytest

try:
    import requests
except ModuleNotFoundError:
    requests = types.ModuleType("requests")

    class RequestException(Exception):
        pass

    class HTTPError(RequestException):
        pass

    class Timeout(RequestException):
        pass

    requests.exceptions = types.SimpleNamespace(
        RequestException=RequestException,
        HTTPError=HTTPError,
        Timeout=Timeout,
    )
    requests.post = None
    requests.get = None
    sys.modules["requests"] = requests


SCRIPT = (
    Path(__file__).parents[1]
    / "skills/visualization/alterlab-scientific-schematics/scripts/generate_schematic_ai.py"
)
SPEC = importlib.util.spec_from_file_location("generate_schematic_ai", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ScientificSchematicGenerator = MODULE.ScientificSchematicGenerator


class FakeResponse:
    def __init__(self, payload=None, content=b"", status_code=200):
        self._payload = payload or {}
        self.content = content
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def atlas_generator():
    return ScientificSchematicGenerator(
        api_key="openrouter-test-key",
        atlas_api_key="atlas-test-key",
        image_provider="atlas",
    )


def test_atlas_generation_submits_once_and_downloads_completed_output(monkeypatch):
    calls = {"post": 0, "prediction_get": 0, "download_get": 0}

    def fake_post(url, **kwargs):
        calls["post"] += 1
        assert url.endswith("/model/generateImage")
        assert kwargs["json"]["model"] == "openai/gpt-image-2/text-to-image"
        return FakeResponse({"code": 200, "data": {"id": "prediction-1"}})

    def fake_get(url, **kwargs):
        if "/prediction/" in url:
            calls["prediction_get"] += 1
            status = "processing" if calls["prediction_get"] == 1 else "completed"
            return FakeResponse({
                "code": 200,
                "data": {
                    "id": "prediction-1",
                    "status": status,
                    "outputs": ["https://cdn.example.test/diagram.png"] if status == "completed" else [],
                },
            })
        calls["download_get"] += 1
        return FakeResponse(content=b"png-bytes")

    monkeypatch.setattr(MODULE.requests, "post", fake_post)
    monkeypatch.setattr(MODULE.requests, "get", fake_get)
    monkeypatch.setattr(MODULE.time, "sleep", lambda _: None)

    assert atlas_generator().generate_image("A scientific flowchart") == b"png-bytes"
    assert calls == {"post": 1, "prediction_get": 2, "download_get": 1}


def test_atlas_failed_prediction_does_not_repeat_paid_post(monkeypatch, tmp_path):
    post_calls = 0

    def fake_post(url, **kwargs):
        nonlocal post_calls
        post_calls += 1
        return FakeResponse({"code": 200, "data": {"id": "prediction-2"}})

    monkeypatch.setattr(MODULE.requests, "post", fake_post)
    monkeypatch.setattr(
        MODULE.requests,
        "get",
        lambda url, **kwargs: FakeResponse({
            "code": 200,
            "data": {"id": "prediction-2", "status": "failed", "outputs": []},
        }),
    )

    result = atlas_generator().generate_iterative(
        "A scientific flowchart",
        str(tmp_path / "diagram.png"),
        iterations=2,
    )

    assert result["success"] is False
    assert len(result["iterations"]) == 1
    assert post_calls == 1


def test_atlas_submission_error_is_not_retried(monkeypatch):
    post_calls = 0

    def fake_post(url, **kwargs):
        nonlocal post_calls
        post_calls += 1
        raise requests.exceptions.Timeout("timed out")

    monkeypatch.setattr(MODULE.requests, "post", fake_post)

    generator = atlas_generator()
    assert generator.generate_image("A scientific flowchart") is None
    assert "timed out" in generator._last_error
    assert post_calls == 1


def test_atlas_provider_requires_atlas_key(monkeypatch):
    monkeypatch.delenv("ATLASCLOUD_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ATLASCLOUD_API_KEY"):
        ScientificSchematicGenerator(
            api_key="openrouter-test-key",
            image_provider="atlas",
        )
