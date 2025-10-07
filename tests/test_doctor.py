import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib
from types import SimpleNamespace

import pytest


def load_doctor(monkeypatch):
    # Ensure we reload module fresh for each test
    if "vidmelt.doctor" in importlib.sys.modules:
        del importlib.sys.modules["vidmelt.doctor"]
    return importlib.import_module("vidmelt.doctor")


def test_doctor_reports_issues(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")

    doctor = load_doctor(monkeypatch)

    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    monkeypatch.setattr(doctor.redis, "from_url", lambda url: SimpleNamespace(ping=lambda: (_ for _ in ()).throw(ConnectionError("down"))))

    class FakeSpec(SimpleNamespace):
        def load_module(self):
            raise ImportError("numba mismatch")

    def fake_import(name):
        if name == "whisper":
            raise ImportError("numba mismatch")
        raise AssertionError("Unexpected import")

    monkeypatch.setattr(doctor.importlib, "import_module", fake_import)

    ok, issues = doctor.run_diagnostics()

    assert not ok
    joined = "\n".join(issues)
    assert "FFmpeg" in joined
    assert "Redis" in joined
    assert "Whisper" in joined
    assert "OPENAI_API_KEY" in joined


def test_doctor_passes_when_dependencies_ok(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    doctor = load_doctor(monkeypatch)

    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/%s" % name)

    class DummyRedis(SimpleNamespace):
        def ping(self):
            return True

    monkeypatch.setattr(doctor.redis, "from_url", lambda url: DummyRedis())

    def fake_import(name):
        if name == "whisper":
            return SimpleNamespace(__name__="whisper")
        raise AssertionError("Unexpected import")

    monkeypatch.setattr(doctor.importlib, "import_module", fake_import)

    ok, issues = doctor.run_diagnostics()

    assert ok
    assert not issues


def test_doctor_skips_redis_in_memory(monkeypatch):
    monkeypatch.setenv("VIDMELT_EVENT_STRATEGY", "in-memory")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    doctor = load_doctor(monkeypatch)

    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/%s" % name)
    monkeypatch.setattr(doctor.importlib, "import_module", lambda name: SimpleNamespace(__name__=name))

    ok, issues = doctor.run_diagnostics()

    assert ok
    assert not any("Redis" in issue for issue in issues)
