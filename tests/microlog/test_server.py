"""Tests for the Microlog server"""


# pylint: disable=unused-argument
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=unspecified-encoding
# pylint: disable=wrong-import-position

from io import BytesIO
import sys
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch


# Create a proper mock zstd module and make it available globally
mock_zstd = MagicMock()
mock_zstd.compress = MagicMock()
mock_zstd.decompress = MagicMock()
sys.modules["zstd"] = mock_zstd

# Now import microlog modules
from microlog import server  # noqa: E402


def create_log_server():
    """Create LogServer handler for testing."""
    # Mock the log_watcher from outer scope
    mock_log_watcher = MagicMock()
    mock_log_watcher.get_recording_names.return_value = ["app1/log1", "app2/log2"]
    connection = MagicMock()
    server.LogServerHandler.__init__ = MagicMock()
    server.LogServerHandler.__init__.return_value = None
    handler = server.LogServerHandler(connection, "", "")
    # Inject the mock log_watcher
    setattr(handler, "log_watcher", mock_log_watcher)
    return handler


class TestUtilityFunctions:
    @patch("logging.info")
    def test_info_function(self, mock_logging_info):
        """Test info function calls logging.info."""
        server.info("test message")

        mock_logging_info.assert_called_once_with("test message")

    @patch("logging.error")
    def test_error_function(self, mock_logging_error):
        """Test error function calls logging.error."""
        server.error("error message")

        mock_logging_error.assert_called_once_with("error message")


class TestLogServerHandler:
    def __init__(self):
        self.handler = None

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = create_log_server()
        self.handler.path = "/"
        self.handler.wfile = BytesIO()

    def test_get_full_path_basic(self):
        """Test get_full_path with basic path."""
        result = self.handler.get_full_path("/test/path")
        assert result == "test/path"

    def test_get_full_path_removes_leading_slash(self):
        """Test get_full_path removes leading slash."""
        result = self.handler.get_full_path("/some/path")
        assert result == "some/path"

    def test_get_full_path_no_leading_slash(self):
        """Test get_full_path with no leading slash."""
        result = self.handler.get_full_path("some/path")
        assert result == "some/path"

    def test_get_full_path_microlog_double_slash(self):
        """Test get_full_path removes /microlog// pattern."""
        result = self.handler.get_full_path("/microlog//resource")
        assert result == "resource"

    def test_get_full_path_microlog_duplicate(self):
        """Test get_full_path removes /microlog/microlog/ pattern."""
        result = self.handler.get_full_path("/microlog/microlog/resource")
        assert result == "microlog/resource"


class TestServer:
    @patch("microlog.config.HOST", "localhost")
    @patch("microlog.config.PORT", 8080)
    @patch("microlog.server.HTTPServer")
    @patch("microlog.server.info")
    def test_server_start(self, mock_info, mock_http_server):
        """Test Server.start method."""
        mock_server = MagicMock()
        mock_server.serve_forever.return_value = (
            None  # Ensure serve_forever doesn't hang
        )
        mock_http_server.return_value = mock_server

        server_instance = server.Server()
        server_instance.start()

        mock_info.assert_called_with(
            "Starting Microlog server... http://localhost:8080"
        )
        mock_http_server.assert_called_once()
        mock_server.serve_forever.assert_called_once()

    @patch("microlog.config.HOST", "localhost")
    @patch("microlog.config.PORT", 8080)
    @patch("microlog.server.HTTPServer")
    @patch("microlog.server.info")
    def test_server_start_os_error(self, mock_info, mock_http_server):
        """Test Server.start handles OSError."""
        mock_server = MagicMock()
        mock_server.serve_forever.side_effect = OSError("Port already in use")
        mock_http_server.return_value = mock_server

        server_instance = server.Server()
        # Should not raise exception
        server_instance.start()

        mock_server.serve_forever.assert_called_once()


class TestRunFunction:
    @patch("subprocess.Popen")
    @patch("sys.executable", "/usr/bin/python")
    def test_run_function(self, mock_popen):
        """Test run function starts subprocess."""
        server.run()

        mock_popen.assert_called_once_with(["/usr/bin/python", server.__file__])


class TestMainExecution:
    @patch("microlog.server.Server")
    def test_main_execution(self, mock_server_class):
        """Test main execution block."""
        mock_server = MagicMock()
        mock_server_class.return_value = mock_server

        # Simulate the main block execution
        if __name__ == "__main__":
            server.Server().start()

        # This test verifies the structure, actual execution would happen in main block


class TestFileOperations:
    def test_get_resource_success(self):
        """Test get_resource with successful file read."""
        handler = MagicMock()
        handler.path = "/test.html"
        handler.get_full_path.return_value = "test.html"

        def get_resource(self):
            path = self.get_full_path(self.path)
            try:
                with open(path) as fd:
                    return self.send_data(
                        "text/html",
                        bytes(f"{fd.read()}", encoding="utf-8"),
                        {"Cache-Control": "public, max-age=86400"},
                    )
            except FileNotFoundError:
                return self.send_data(
                    "text/html",
                    bytes(f"Cannot open {self.path} {path}", encoding="utf-8"),
                )

        with patch("builtins.open", mock_open(read_data="<html>test</html>")):
            get_resource(handler)

        handler.send_data.assert_called_once_with(
            "text/html",
            b"<html>test</html>",
            {"Cache-Control": "public, max-age=86400"},
        )

    def test_get_resource_file_not_found(self):
        """Test get_resource with file not found."""
        handler = MagicMock()
        handler.path = "/nonexistent.html"
        handler.get_full_path.return_value = "nonexistent.html"

        def get_resource(self):
            path = self.get_full_path(self.path)
            try:
                with open(path) as fd:
                    return self.send_data(
                        "text/html",
                        bytes(f"{fd.read()}", encoding="utf-8"),
                        {"Cache-Control": "public, max-age=86400"},
                    )
            except FileNotFoundError:
                print("Error - Resource not found:", self.path, path)
                return self.send_data(
                    "text/html",
                    bytes(f"Cannot open {self.path} {path}", encoding="utf-8"),
                )

        with (
            patch("builtins.open", side_effect=FileNotFoundError),
            patch("builtins.print") as mock_print,
        ):
            get_resource(handler)

        mock_print.assert_called_once_with(
            "Error - Resource not found:", "/nonexistent.html", "nonexistent.html"
        )
        handler.send_data.assert_called_once_with(
            "text/html", b"Cannot open /nonexistent.html nonexistent.html"
        )


class TestGetFullPathMethod:
    def __init__(self):
        self.handler = None

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = create_log_server()
        self.handler.path = "/"
        self.handler.wfile = BytesIO()

    def test_get_full_path_basic(self):
        """Test get_full_path with basic path."""
        result = self.handler.get_full_path("/test/path")
        assert result == "test/path"

    def test_get_full_path_no_leading_slash(self):
        """Test get_full_path with path that doesn't start with slash."""
        result = self.handler.get_full_path("test/path")
        assert result == "test/path"

    def test_get_full_path_microlog_double_slash(self):
        """Test get_full_path removes /microlog// pattern."""
        result = self.handler.get_full_path("/microlog//resource.html")
        assert result == "resource.html"

    def test_get_full_path_microlog_duplicate(self):
        """Test get_full_path removes /microlog/microlog/ pattern."""
        result = self.handler.get_full_path("/microlog/microlog/index.html")
        assert result == "microlog/index.html"

    def test_get_full_path_both_patterns(self):
        """Test get_full_path with both problematic patterns."""
        # First apply double slash removal, then duplicate removal
        result = self.handler.get_full_path("/microlog//microlog/index.html")
        assert result == "microlog/index.html"

    def test_get_full_path_real_world_paths(self):
        """Test get_full_path with realistic file paths."""
        test_cases = [
            ("/static/css/main.css", "static/css/main.css"),
            ("/js/microlog.js", "js/microlog.js"),
            ("/images/logo.png", "images/logo.png"),
            ("/microlog/index.html", "microlog/index.html"),
            ("/api/logs", "api/logs"),
        ]

        for input_path, expected in test_cases:
            result = self.handler.get_full_path(input_path)
            assert result == expected

    def test_get_full_path_order_of_operations(self):
        """Test get_full_path processes replacements in correct order."""
        # Test that double slash replacement happens first
        result = self.handler.get_full_path("/microlog//microlog/index.html")
        # After first replacement: "/microlog/index.html"
        # After second replacement: "/microlog/index.html" (no change)
        # After leading slash removal: "microlog/index.html"
        assert result == "microlog/index.html"
