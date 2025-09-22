"""Tests for microlog.analyse."""

import openai
import pytest

import microlog.analyse as analyse


class DummyCallSite:
    """A dummy CallSite for testing purposes."""
    def __init__(self, name):
        self.name = name

class DummyCall:
    """A dummy Call for testing purposes."""
    def __init__(self, name, duration):
        self.call_site = DummyCallSite(name)
        self.duration = duration

class DummyRecording:
    """A dummy Recording for testing purposes."""
    def __init__(self, calls):
        self.calls = calls

def test_analyse_recording_no_api_key(monkeypatch):
    """Test analyse_recording returns error if no API key is set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(openai.OpenAIError):
        result = analyse.analyse_recording(DummyRecording([]))
        assert "Could not find an OpenAI key" in result
