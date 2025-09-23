"""
Stub module for the 'js' package used in PyScript/PyOdide environments.

This module provides mock implementations for JavaScript functionality
that would normally be available through the 'js' module in PyScript/PyOdide.
This allows the code to run in regular Python environments for testing,
development, or when PyScript/PyOdide is not available.
"""

# pylint: disable=unused-argument
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=redefined-builtin


from typing import Any
from typing import Dict
from typing import Optional
from typing import Union
from typing import overload


class MockJQuery:
    """Mock implementation of jQuery functionality."""

    def __init__(self, selector: Union[str, "MockWindow"] = ""):
        self.selector = selector
        self.length = 0

    def __call__(self, selector: Union[str, "MockWindow"]) -> "MockJQuery":
        return MockJQuery(selector)

    @overload
    def val(self) -> str: ...

    @overload
    def val(self, value: str) -> "MockJQuery": ...

    def val(self, value: Optional[str] = None) -> Union[str, "MockJQuery"]:
        if value is None:
            return ""
        return self

    def html(self, content: Optional[str] = None) -> Union[Any, "MockJQuery"]:
        return self

    @overload
    def text(self) -> str: ...

    @overload
    def text(self, content: str) -> "MockJQuery": ...

    def text(self, content: Optional[str] = None) -> Union[str, "MockJQuery"]:
        if content is None:
            return "Mock text"
        return self

    def css(
        self, prop: str, value: Union[str, int, float, None] = None
    ) -> Union[Any, "MockJQuery"]:
        return self

    @overload
    def attr(self, name: str) -> str: ...

    @overload
    def attr(self, name: str, value: Union[str, int, float]) -> "MockJQuery": ...

    def attr(
        self, name: str, value: Union[str, int, float, None] = None
    ) -> Union[str, "MockJQuery"]:
        if value is None:
            # Return a string that can be converted to int/float
            return "0"
        # For some canvas operations, they expect attr(name, value) or 0 to work
        # We need to make this work with both chaining and numeric contexts
        return self

    def prop(self, name: str, value: Optional[Any] = None) -> Union[Any, "MockJQuery"]:
        return self

    def addClass(self, className: str) -> "MockJQuery":
        return self

    def removeClass(self, className: str) -> "MockJQuery":
        return self

    def append(self, *content: Any) -> "MockJQuery":
        return self

    def appendTo(self, target: Any) -> "MockJQuery":
        return self

    def prepend(self, *content: Any) -> "MockJQuery":
        return self

    def remove(self) -> "MockJQuery":
        return self

    def tabs(self, *args: Any) -> Any:
        if args:
            # When called with arguments like tabs("option", "active"), return a value
            return 0
        return self

    def lower(self) -> "MockJQuery":
        return self

    def click(self, handler: Any = None) -> "MockJQuery":
        return self

    def on(self, event: str, handler: Any) -> "MockJQuery":
        return self

    def draggable(self) -> "MockJQuery":
        return self

    def eq(self, index: int) -> "MockJQuery":
        return MockJQuery(f"eq({index})")

    def parent(self) -> "MockJQuery":
        return self

    def closest(self, selector: str) -> "MockJQuery":
        return self

    def find(self, selector: str) -> "MockJQuery":
        return self

    def height(self) -> int:
        return 600

    def empty(self) -> "MockJQuery":
        return self

    def width(self) -> int:
        return 800

    def __getitem__(self, index: int) -> "MockJQuery":
        """Allow indexing like jQuery objects."""
        return MockJQuery(f"[{index}]")

    def __bool__(self) -> bool:
        """Make jQuery objects falsy when they represent empty results."""
        # For canvas.attr("width", value) or 0 to work properly
        return self.length > 0

    def change(self, handler: Any) -> "MockJQuery":
        return self

    def keyup(self, handler: Any) -> "MockJQuery":
        return self

    def offset(self) -> Any:
        """Mock implementation of jQuery offset()."""

        class MockOffset:
            def __init__(self) -> None:
                self.top = 0.0
                self.left = 0.0

        return MockOffset()

    def position(self) -> Any:
        """Mock implementation of jQuery position()."""

        class MockPosition:
            def __init__(self) -> None:
                self.top = 0.0
                self.left = 0.0

        return MockPosition()

    def getContext(self, context_type: str = "2d") -> Any:
        """Mock implementation of canvas getContext()."""

        class MockContext:
            def __init__(self) -> None:
                pass

            def fill(self) -> None:
                pass

            def rect(self, x: float, y: float, w: float, h: float) -> None:
                pass

            def fillRect(self, x: float, y: float, w: float, h: float) -> None:
                pass

            def drawImage(self, image: Any, x: float, y: float, w: float, h: float) -> None:
                pass

            def beginPath(self) -> None:
                pass

            def moveTo(self, x: float, y: float) -> None:
                pass

            def lineTo(self, x: float, y: float) -> None:
                pass

            def stroke(self) -> None:
                pass

            def fillText(self, text: str, x: float, y: float, w: float) -> None:
                pass

        return MockContext()

    @staticmethod
    def get(url: str, callback: Any) -> None:
        """Mock implementation of jQuery.get()."""
        # Simulate successful response by calling the callback
        if callback:
            callback(None)


class MockLocalStorage:
    """Mock implementation of localStorage functionality."""

    def __init__(self) -> None:
        self._storage: Dict[str, str] = {}

    @overload
    def getItem(self, key: str) -> Optional[str]: ...

    @overload
    def getItem(self, key: str, default: str) -> str: ...

    def getItem(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._storage.get(key, default)

    def setItem(self, key: str, value: Union[str, int, float]) -> None:
        self._storage[key] = str(value)

    def removeItem(self, key: str) -> None:
        self._storage.pop(key, None)

    def clear(self) -> None:
        self._storage.clear()


def parseFloat(value: Union[str, int, float]) -> float:
    """Mock implementation of JavaScript parseFloat."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def setTimeout(callback: Any, delay: int = 0) -> int:
    """Mock implementation of JavaScript setTimeout."""
    # In a real implementation, you might want to use threading.Timer
    # For now, just return a mock timer ID
    return 1


class MockLocation:
    """Mock implementation of window.location functionality."""

    def reload(self) -> None:
        """Mock implementation of location.reload()."""


class MockDocumentLocation:
    """Mock implementation of document.location functionality."""

    def __init__(self) -> None:
        self.hash = ""


class MockDocument:
    """Mock implementation of document functionality."""

    def __init__(self) -> None:
        self.location: Any = MockDocumentLocation()


class MockWindow:
    """Mock implementation of window functionality."""

    def __init__(self) -> None:
        self.location = MockLocation()


class MockHistory:
    """Mock implementation of history functionality."""

    def pushState(self, state: Any, title: str, url: str) -> None:
        """Mock implementation of history.pushState()."""


class MockConsole:
    """Mock implementation of console functionality."""

    def log(self, *args: Any) -> None:
        """Mock implementation of console.log()."""

    def error(self, *args: Any) -> None:
        """Mock implementation of console.error()."""

    def warn(self, *args: Any) -> None:
        """Mock implementation of console.warn()."""


# Mock object() function
def object() -> Dict[str, Any]:
    """Mock implementation of JavaScript object() constructor."""
    return {}


def optimizedDrawPolygon(
    context: Any, color: str, lineWidth: float, coordinates: str
) -> Any:
    """Mock implementation of optimizedDrawPolygon function."""
    return None


def optimizedFillRects(context: Any, coordinates: str) -> Any:
    """Mock implementation of optimizedFillRects function."""
    return None


def optimizedDrawLines(
    context: Any, lineWidth: float, color: str, coordinates: str
) -> Any:
    """Mock implementation of optimizedDrawLines function."""
    return None


def optimizedDrawTexts(context: Any, coordinates: str) -> Any:
    """Mock implementation of optimizedDrawTexts function."""
    return None


def load_binary(url: str, callback: Any) -> None:
    """Mock implementation of load_binary function."""


def alert(message: str) -> None:
    """Mock implementation of JavaScript alert function."""


def circle(
    context: Any,
    x: float,
    y: float,
    radius: float,
    fill: str,
    lineWidth: float,
    color: str,
) -> None:
    """Mock implementation of circle function."""


def draw_graph(data: str) -> None:
    """Mock implementation of custom JavaScript draw_graph function."""
    # This would normally draw a graph in the browser
    # For testing/development, we just parse the JSON to validate it


# Global mock objects
jQuery = MockJQuery()
localStorage = MockLocalStorage()
window = MockWindow()
history = MockHistory()
document = MockDocument()
console = MockConsole()
development_location = ""
