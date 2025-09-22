"""Unit tests for the Status model."""

from microlog.models import Status


class TestStatus:
    """Unit tests for the Status model."""

    def test_init_basic(self):
        """Test basic Status initialization."""
        status = Status(
            when=123.456789,
            cpu=45.67,
            system_cpu=78.90,
            memory=1024,
            memory_total=8192,
            memory_free=4096,
            module_count=50,
            object_count=1000,
        )

        assert status.when == 123.457  # rounded to 3 decimals
        assert status.cpu == 46  # rounded to nearest integer
        assert status.system_cpu == 78.90  # not rounded
        assert status.memory == 1024
        assert status.memory_total == 8192
        assert status.memory_free == 4096
        assert status.module_count == 50
        assert status.object_count == 1000
        assert status.duration == 0.0

    def test_init_rounding_precision(self):
        """Test precision rounding for when and cpu."""
        status = Status(
            when=123.9876543210,
            cpu=99.7654321,
            system_cpu=88.123456,
            memory=2048,
            memory_total=16384,
            memory_free=8192,
            module_count=75,
            object_count=2000,
        )

        assert status.when == 123.988  # rounded to 3 decimals
        assert status.cpu == 100  # rounded to nearest integer
        assert status.system_cpu == 88.123456  # not rounded

    def test_init_negative_values(self):
        """Test Status with negative values."""
        status = Status(
            when=100.0,
            cpu=-5.7,
            system_cpu=-10.5,
            memory=-512,
            memory_total=4096,
            memory_free=2048,
            module_count=25,
            object_count=500,
        )

        assert status.cpu == -6  # rounded to nearest integer
        assert status.system_cpu == -10.5
        assert status.memory == -512

    def test_init_zero_values(self):
        """Test Status with zero values."""
        status = Status(
            when=0.0,
            cpu=0.0,
            system_cpu=0.0,
            memory=0,
            memory_total=0,
            memory_free=0,
            module_count=0,
            object_count=0,
        )

        assert status.when == 0.0
        assert status.cpu == 0
        assert status.system_cpu == 0.0
        assert all(
            getattr(status, attr) == 0
            for attr in [
                "memory",
                "memory_total",
                "memory_free",
                "module_count",
                "object_count",
            ]
        )

    def test_duration_attribute_exists(self):
        """Test that Status instances have duration attribute."""
        status = Status(
            when=100.0,
            cpu=50.0,
            system_cpu=75.0,
            memory=1024,
            memory_total=4096,
            memory_free=2048,
            module_count=50,
            object_count=1000,
        )

        assert hasattr(status, "duration")
        assert status.duration == 0.0
