"""Unit tests for the Marker model."""

from microlog.models import CallSite
from microlog.models import Marker
from microlog.models import Model
from microlog.models import Stack


class TestMarker:
    """Unit tests for the Marker model."""
    def __init__(self):
        self.call_site1 = CallSite("file1.py", 10, "module1.func1")
        self.call_site2 = CallSite("file2.py", 20, "module2.func2")
        self.stack = Stack(when=100.0, call_sites=[self.call_site1, self.call_site2])

    def test_init_basic(self):
        """Test basic Marker initialization."""
        marker = Marker(
            kind=1,
            when=123.456789,
            message="test message",
            stack=self.stack,
            duration=0.987654,
        )

        assert marker.kind == 1
        assert marker.when == 123.457  # rounded to 3 decimals
        assert marker.message == "test message"
        assert marker.stack == self.stack
        assert marker.duration == 0.987654  # duration not rounded in init

    def test_init_default_duration(self):
        """Test Marker initialization with default duration."""
        marker = Marker(kind=2, when=123.456, message="test message", stack=self.stack)

        assert marker.duration == 0.1

    def test_init_rounding_precision(self):
        """Test that when is properly rounded to 3 decimal places."""
        marker = Marker(kind=1, when=123.4567890123, message="test", stack=self.stack)

        assert marker.when == 123.457

    def test_inheritance_from_model(self):
        """Test that Marker inherits from Model."""
        assert issubclass(Marker, Model)

        marker = Marker(1, 100.0, "test", self.stack)
        assert isinstance(marker, Model)

    def test_marker_attributes_immutable_after_creation(self):
        """Test marker attributes can be modified after creation."""
        marker = Marker(1, 100.0, "test", self.stack)

        # These should be allowed (no immutability enforced)
        marker.kind = 2
        marker.when = 200.0
        marker.message = "new message"
        marker.duration = 0.8

        assert marker.kind == 2
        assert marker.when == 200.0
        assert marker.message == "new message"
        assert marker.duration == 0.8
