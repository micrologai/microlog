"""Unit tests for the Stack model."""

from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from unittest.mock import patch

import pytest

from microlog.models import CALLSITE_IGNORE
from microlog.models import CallSite
from microlog.models import Stack


class TestStack:
    """Unit tests for the Stack model."""

    def __init__(self):
        """Set up test fixtures."""
        self.call_site1 = CallSite("file1.py", 10, "module1.class1.func1")
        self.call_site2 = CallSite("file2.py", 20, "module2.class2.func2")

    def test_init_basic(self):
        """Test basic Stack initialization."""
        stack = Stack(when=123.456, index=5)
        assert stack.index == 5
        assert stack.when == 123.456
        assert stack.call_sites == []

    def test_init_with_call_sites(self):
        """Test Stack initialization with call_sites."""
        call_sites = [self.call_site1, self.call_site2]
        stack = Stack(when=123.456, index=5, call_sites=call_sites)
        assert stack.index == 5
        assert stack.when == 123.456
        assert stack.call_sites == call_sites

    @patch.object(Stack, "walk_stack")
    @patch.object(Stack, "call_site_from_frame")
    def test_init_with_ignore_call_site(self, mock_call_site_from_frame, mock_walk_stack):
        """Test Stack initialization skips CALLSITE_IGNORE."""
        mock_frame1 = MagicMock()
        mock_frame2 = MagicMock()
        mock_frame3 = MagicMock()
        mock_walk_stack.return_value = [
            (mock_frame1, 10),
            (mock_frame2, 20),
            (mock_frame3, 30),
        ]
        mock_call_site_from_frame.side_effect = [
            self.call_site1,
            CALLSITE_IGNORE,
            self.call_site2,
        ]
        stack = Stack(when=123.456, start_frame=mock_frame1)
        assert len(stack.call_sites) == 2
        assert stack.call_sites[0] == self.call_site1
        assert stack.call_sites[1] == self.call_site2

    @patch("traceback.walk_stack")
    def test_walk_stack(self, mock_walk_stack):
        """Test walk_stack method."""
        mock_frame = MagicMock()
        mock_walk_stack.return_value = [("frame1", 10), ("frame2", 20), ("frame3", 30)]
        stack = Stack()
        result = stack.walk_stack(mock_frame)
        mock_walk_stack.assert_called_once_with(mock_frame)
        # Should be reversed
        assert result == [("frame3", 30), ("frame2", 20), ("frame1", 10)]

    def test_call_site_from_frame_main_module(self):
        """Test call_site_from_frame with __main__ module."""
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__file__": "script.py", "__name__": "__main__"}
        mock_frame.f_code.co_name = "main"
        mock_frame.f_locals = {}
        with patch("sys.argv", ["path/to/script.py"]):
            result = Stack().call_site_from_frame(mock_frame, 10)
        assert result.name == "path.to.script..main"

    def test_call_site_from_frame_with_self(self):
        """Test call_site_from_frame with self in locals."""
        mock_instance = MagicMock()
        mock_instance.__class__.__name__ = "TestClass"
        mock_instance.__module__ = "test.module"
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__file__": "test.py", "__name__": "test_module"}
        mock_frame.f_code.co_name = "method"
        mock_frame.f_locals = {"self": mock_instance}
        result = Stack().call_site_from_frame(mock_frame, 15)
        assert result.name == "test.module.TestClass.method"

    def test_call_site_from_frame_self_exception(self):
        """Test call_site_from_frame when self access raises exception."""
        mock_instance = MagicMock()
        mock_instance.__class__.__name__ = "TestClass"
        type(mock_instance).__module__ = PropertyMock(
            side_effect=Exception("No module")
        )
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__file__": "test.py", "__name__": "test_module"}
        mock_frame.f_code.co_name = "method"
        mock_frame.f_locals = {"self": mock_instance}
        result = Stack().call_site_from_frame(mock_frame, 15)
        assert result.name == "unknown.Unknown.method"

    @patch.object(Stack, "ignore")
    def test_call_site_from_frame_ignore_module(self, mock_ignore):
        """Test call_site_from_frame returns CALLSITE_IGNORE for ignore modules."""
        mock_ignore.return_value = True
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__file__": "test.py", "__name__": "ignore_module"}
        mock_frame.f_code.co_name = "function"
        mock_frame.f_locals = {}
        result = Stack().call_site_from_frame(mock_frame, 10)
        assert result is CALLSITE_IGNORE

    @patch("inspect.getmro")
    def test_call_site_from_frame_inner_function(self, mock_getmro):
        """Test call_site_from_frame with 'inner' function and 'func' in locals."""
        mock_function = MagicMock()
        mock_function.__name__ = "actual_function"
        mock_function.__module__ = "actual.module"
        setattr(mock_function, "__class__", MagicMock())
        mock_getmro.return_value = [MagicMock()]
        mock_getmro.return_value[0].__name__ = "FunctionClass"
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__file__": "test.py", "__name__": "wrapper_module"}
        mock_frame.f_code.co_name = "inner"
        mock_frame.f_locals = {"func": mock_function}
        with patch.object(Stack, "ignore", return_value=False):
            result = Stack().call_site_from_frame(mock_frame, 10)
        assert result.name == "actual.module.FunctionClass.actual_function"

    def test_iter(self):
        """Test Stack iteration."""
        stack = Stack(call_sites=[self.call_site1, self.call_site2])
        result = list(stack)
        assert result == [self.call_site1, self.call_site2]

    def test_len(self):
        """Test Stack length."""
        stack = Stack(call_sites=[self.call_site1, self.call_site2])
        assert len(stack) == 2

    def test_len_empty(self):
        """Test Stack length when empty."""
        stack = Stack(call_sites=[])
        assert len(stack) == 0

    def test_getitem(self):
        """Test Stack indexing."""
        stack = Stack(call_sites=[self.call_site1, self.call_site2])
        assert stack[0] == self.call_site1
        assert stack[1] == self.call_site2

    def test_getitem_negative_index(self):
        """Test Stack negative indexing."""
        stack = Stack(call_sites=[self.call_site1, self.call_site2])
        assert stack[-1] == self.call_site2
        assert stack[-2] == self.call_site1

    def test_getitem_index_error(self):
        """Test Stack indexing out of bounds."""
        stack = Stack(call_sites=[self.call_site1])
        with pytest.raises(IndexError):
            _ = stack[5]

    def test_repr(self):
        """Test Stack string representation."""
        stack = Stack(index=3, call_sites=[self.call_site1, self.call_site2])
        result = repr(stack)
        expected = "<Stack 3 module1.class1.func1 module2.class2.func2\n>"
        assert result == expected

    def test_repr_empty_call_sites(self):
        """Test Stack string representation with empty call_sites."""
        stack = Stack(index=1, call_sites=[])
        result = repr(stack)
        assert result == "<Stack 1 \n>"

    def test_call_site_from_frame_no_name(self):
        """Test call_site_from_frame when __name__ is missing."""
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__file__": "test.py"}  # No __name__
        mock_frame.f_code.co_name = "test_function"
        mock_frame.f_locals = {}
        result = Stack().call_site_from_frame(mock_frame, 42)
        assert result.name == "..test_function"  # Empty module name
