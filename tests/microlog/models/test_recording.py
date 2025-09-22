"""Unit tests for microlog.models.Recording class."""
import pickle
import sys
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch


# Create a proper mock zstd module and make it available globally
mock_zstd = MagicMock()
mock_zstd.compress = MagicMock()
mock_zstd.decompress = MagicMock()
sys.modules["zstd"] = mock_zstd

# Now import microlog modules
from microlog import config  # noqa: E402  pylint: disable=wrong-import-position
from microlog.models import Call  # noqa: E402  pylint: disable=wrong-import-position
from microlog.models import CallSite  # noqa: E402  pylint: disable=wrong-import-position
from microlog.models import Recording  # noqa: E402  pylint: disable=wrong-import-position
from microlog.models import Stack  # noqa: E402  pylint: disable=wrong-import-position
from microlog.models import Status  # noqa: E402  pylint: disable=wrong-import-position


class TestRecording:
    """Tests for the Recording class."""
    def test_init_basic(self):
        """Test basic Recording initialization."""
        recording = Recording()

        assert recording.calls == []
        assert recording.markers == []
        assert recording.statuses == []
        assert isinstance(recording.calls, list)
        assert isinstance(recording.markers, list)
        assert isinstance(recording.statuses, list)

    def test_print_in_block(self):
        """Test print_in_block method output formatting."""
        recording = Recording()
        message = "Test message"

        with patch("sys.stdout.write") as mock_write:
            recording.print_in_block(message)

            expected_calls = [
                call(f"┏{'━' * (len(message) + 2)}┓\n"),
                call(f"┃ {message} ┃\n"),
                call(f"┗{'━' * (len(message) + 2)}┛\n"),
            ]
            mock_write.assert_has_calls(expected_calls)

    def test_print_in_block_long_message(self):
        """Test print_in_block with a long message."""
        recording = Recording()
        message = (
            "This is a very long test message that should still be formatted correctly"
        )

        with patch("sys.stdout.write") as mock_write:
            recording.print_in_block(message)

            # Verify the box is properly sized
            box_width = len(message) + 2
            expected_calls = [
                call(f"┏{'━' * box_width}┓\n"),
                call(f"┃ {message} ┃\n"),
                call(f"┗{'━' * box_width}┛\n"),
            ]
            mock_write.assert_has_calls(expected_calls)

    def test_print_in_block_empty_message(self):
        """Test print_in_block with empty message."""
        recording = Recording()
        message = ""

        with patch("sys.stdout.write") as mock_write:
            recording.print_in_block(message)

            expected_calls = [call("┏━━┓\n"), call("┃  ┃\n"), call("┗━━┛\n")]
            mock_write.assert_has_calls(expected_calls)

    @patch("microlog.config.SERVER", "http://localhost:8080", create=True)
    def test_show_details(self):
        """Test show_details method."""
        recording = Recording()
        identifier = "test app/2023_12_25_10_30_45"

        with patch.object(recording, "print_in_block") as mock_print:
            recording.show_details(identifier)

            expected_url = "http://localhost:8080#test_app/2023_12_25_10_30_45"
            mock_print.assert_called_once_with(f"Microlog: {expected_url}")

    @patch("microlog.config.SERVER", "https://microlog.example.com", create=True)
    def test_show_details_with_spaces(self):
        """Test show_details method with spaces in identifier."""
        recording = Recording()
        identifier = "my test app/2023 12 25 10 30 45"

        with patch.object(recording, "print_in_block") as mock_print:
            recording.show_details(identifier)

            expected_url = (
                "https://microlog.example.com#my_test_app/2023_12_25_10_30_45"
            )
            mock_print.assert_called_once_with(f"Microlog: {expected_url}")

    @patch("sys.argv", ["test_script.py"])
    def test_get_application_from_argv(self):
        """Test get_application when application is None."""
        recording = Recording()

        result = recording.get_application()

        assert result == "test_script"

    @patch("sys.argv", ["/very/long/path/to/my/script.py"])
    def test_get_application_path_truncation(self):
        """Test get_application truncates long paths to last 3 components."""
        recording = Recording()

        result = recording.get_application()

        assert result == "to-my-script"

    @patch("datetime.datetime")
    def test_get_identifier(self, mock_datetime):
        """Test get_identifier method."""
        recording = Recording()
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2023_12_25_10_30_45"
        mock_datetime.now.return_value = mock_now

        with patch.object(recording, "get_application", return_value="test_app"):
            result = recording.get_identifier()

            assert result == "test_app/2023_12_25_10_30_45"
            mock_datetime.now.assert_called_once()
            mock_now.strftime.assert_called_once_with("%Y_%m_%d_%H_%M_%S")

    def test_add_status_basic(self):
        """Test add_status method basic functionality."""
        recording = Recording()

        recording.add_status(
            when=123.456,
            cpu=50.0,
            system_cpu=75.0,
            memory=1024,
            memory_total=8192,
            memory_free=4096,
            module_count=10,
            object_count=100,
        )

        assert len(recording.statuses) == 1
        status = recording.statuses[0]
        assert status.when == 123.456
        assert status.cpu == 50
        assert status.system_cpu == 75.0
        assert status.memory == 1024

    def test_add_status_duplicate_prevention(self):
        """Test add_status prevents duplicate similar statuses."""
        recording = Recording()

        # Add first status
        recording.add_status(
            when=123.0,
            cpu=50.0,
            system_cpu=75.0,
            memory=1024,
            memory_total=8192,
            memory_free=4096,
            module_count=10,
            object_count=100,
        )

        # Add similar status (should be skipped)
        recording.add_status(
            when=124.0,  # Different time, but other values same
            cpu=50.0,
            system_cpu=75.0,
            memory=1024,
            memory_total=8192,
            memory_free=4096,
            module_count=10,
            object_count=100,
        )

        # Should still have only 1 status due to similarity check
        assert len(recording.statuses) == 1

    def test_add_status_different_values(self):
        """Test add_status adds different statuses."""
        recording = Recording()

        # Add first status
        recording.add_status(
            when=123.0,
            cpu=50.0,
            system_cpu=75.0,
            memory=1024,
            memory_total=8192,
            memory_free=4096,
            module_count=10,
            object_count=100,
        )

        # Add different status
        recording.add_status(
            when=124.0,
            cpu=60.0,  # Different CPU
            system_cpu=85.0,
            memory=2048,  # Different memory
            memory_total=8192,
            memory_free=4096,
            module_count=10,
            object_count=100,
        )

        # Should have 2 statuses
        assert len(recording.statuses) == 2

    def test_add_call_basic(self):
        """Test add_call method basic functionality."""
        recording = Recording()
        call_site = CallSite("test.py", 42, "test_function")
        caller_site = CallSite("main.py", 10, "main")

        recording.add_call(
            when=123.456,
            thread_id=1,
            call_site=call_site,
            caller_site=caller_site,
            depth=2,
            duration=0.5,
        )

        assert len(recording.calls) == 1
        first_call = recording.calls[0]
        assert first_call.when == 123.456
        assert first_call.thread_id == 1
        assert first_call.call_site == call_site
        assert first_call.caller_site == caller_site
        assert first_call.depth == 2
        assert first_call.duration == 0.5

    def test_add_call_multiple(self):
        """Test adding multiple calls."""
        recording = Recording()
        call_site1 = CallSite("test1.py", 42, "test_function1")
        caller_site1 = CallSite("main.py", 10, "main")
        call_site2 = CallSite("test2.py", 24, "test_function2")
        caller_site2 = CallSite("main.py", 15, "main")

        recording.add_call(123.0, 1, call_site1, caller_site1, 1, 0.5)
        recording.add_call(124.0, 1, call_site2, caller_site2, 2, 1.0)

        assert len(recording.calls) == 2
        assert recording.calls[0].call_site == call_site1
        assert recording.calls[1].call_site == call_site2

    def test_add_marker_basic(self):
        """Test add_marker method basic functionality."""
        recording = Recording()
        stack = Stack(123.0, None, 0, [])

        recording.add_marker(
            kind=config.EVENT_KIND_ERROR,
            when=123.456,
            message="Test error message",
            stack=stack,
            duration=0.1,
        )

        assert len(recording.markers) == 1
        marker = recording.markers[0]
        assert marker.kind == config.EVENT_KIND_ERROR
        assert marker.when == 123.456
        assert marker.message == "Test error message"
        assert marker.stack == stack
        assert marker.duration == 0.1

    def test_add_marker_message_internalization(self):
        """Test that add_marker internalizes message strings."""
        recording = Recording()
        stack = Stack(123.0, None, 0, [])

        # Add same message twice
        recording.add_marker(config.EVENT_KIND_INFO, 123.0, "Same message", stack, 0.1)
        recording.add_marker(config.EVENT_KIND_INFO, 124.0, "Same message", stack, 0.1)

        assert len(recording.markers) == 2
        # Both markers should have the same internalized string object
        assert recording.markers[0].message is recording.markers[1].message

    def test_load_method(self):
        """Test load method functionality."""
        # Create a recording with some data
        original_recording = Recording()
        original_recording.calls = [
            Call(
                123.0,
                1,
                CallSite("test.py", 42, "test"),
                CallSite("main.py", 10, "main"),
                1,
                0.5,
            )
        ]
        original_recording.statuses = [
            Status(123.0, 50.0, 75.0, 1024, 8192, 4096, 10, 100)
        ]

        # Pickle it
        pickled_data = pickle.dumps(original_recording)

        # Create new recording and load data
        new_recording = Recording()

        with patch("builtins.print"):
            new_recording.load(pickled_data)

            # Verify data was loaded
            assert len(new_recording.calls) == 1
            assert len(new_recording.statuses) == 1
            assert new_recording.calls[0].when == 123.0
            assert new_recording.statuses[0].when == 123.0

    @patch("microlog.config.fs", create=True)
    @patch("zstd.compress")
    @patch("pickle.dumps")
    def test_save_method(self, mock_pickle_dumps, mock_zstd_compress, mock_fs):
        """Test save method functionality."""
        recording = Recording()
        mock_pickle_dumps.return_value = b"pickled_data"
        mock_zstd_compress.return_value = b"compressed_data"
        mock_file = MagicMock()
        mock_fs.open.return_value.__enter__.return_value = mock_file

        with patch.object(
            recording, "get_identifier", return_value="test_app/2023_12_25_10_30_45"
        ):
            with patch.object(
                recording,
                "get_log_path",
                return_value="/tmp/logs/test_app/2023_12_25_10_30_45.zip",
            ):
                with patch.object(recording, "show_details") as mock_show_details:
                    with patch.object(recording, "notify_server") as mock_notify_server:
                        recording.save()

                    # Verify pickle and compression
                    mock_pickle_dumps.assert_called_once_with(recording)
                    mock_zstd_compress.assert_called_once_with(b"pickled_data")

                    # Verify file operations
                    mock_fs.makedir.assert_called_once_with(
                        "/tmp/logs/test_app", exist_ok=True
                    )
                    mock_fs.open.assert_called_once_with(
                        "/tmp/logs/test_app/2023_12_25_10_30_45.zip", "wb"
                    )
                    mock_file.write.assert_called_once_with(b"compressed_data")

                    # Verify show_details was called
                    mock_show_details.assert_called_once_with(
                        "test_app/2023_12_25_10_30_45"
                    )

                    # Verify notify_server was called
                    mock_notify_server.assert_called_once_with(
                        "test_app/2023_12_25_10_30_45"
                    )

    def test_load_empty_recording(self):
        """Test loading an empty recording."""
        empty_recording = Recording()
        pickled_data = pickle.dumps(empty_recording)

        new_recording = Recording()

        with patch("builtins.print"):
            new_recording.load(pickled_data)

            assert len(new_recording.calls) == 0
            assert len(new_recording.markers) == 0
            assert len(new_recording.statuses) == 0

    def test_add_call_default_duration(self):
        """Test add_call with default duration."""
        recording = Recording()
        call_site = CallSite("test.py", 42, "test_function")
        caller_site = CallSite("main.py", 10, "main")

        recording.add_call(123.0, 1, call_site, caller_site, 1)  # No duration specified

        assert len(recording.calls) == 1
        assert recording.calls[0].duration == 0.0

    def test_add_marker_default_duration(self):
        """Test add_marker with default duration."""
        recording = Recording()
        stack = Stack(123.0, None, 0, [])

        recording.add_marker(
            config.EVENT_KIND_INFO, 123.0, "Test message", stack
        )  # No duration specified

        assert len(recording.markers) == 1
        assert recording.markers[0].duration == 0.1
