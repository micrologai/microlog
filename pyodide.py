"""
Stub module for the 'pyodide' package used in PyScript/PyOdide environments.

This module provides mock implementations for PyOdide functionality
that would normally be available through the 'pyodide' module in PyScript/PyOdide.
This allows the code to run in regular Python environments for testing,
development, or when PyScript/PyOdide is not available.
"""

from typing import Any
from typing import Callable


class MockFFI:
    """Mock implementation of PyOdide FFI (Foreign Function Interface)."""

    @staticmethod
    def create_proxy(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Mock implementation of pyodide.ffi.create_proxy().

        In PyOdide, create_proxy creates a JavaScript-compatible proxy
        for Python functions so they can be used as event handlers.
        For testing/development, we just return the original function.

        Args:
            func: The Python function to wrap

        Returns:
            The original function (no wrapping needed outside PyOdide)
        """
        return func


# Create the ffi mock object
ffi = MockFFI()


class MockHTTPResponse:
    def __init__(self, data):
        self._data = data
    
    async def bytes(self):
        return self._data
    
    async def text(self):
        return self._data.decode('utf-8') if isinstance(self._data, bytes) else str(self._data)

class MockAbortError(Exception):
    pass

class MockHTTP:
    @staticmethod
    async def pyfetch(url):
        return MockHTTPResponse(b"mock data")
    
    AbortError = MockAbortError

http = MockHTTP()
