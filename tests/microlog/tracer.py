#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import threading
import sys
import unittest

from microlog import config
from microlog import symbols
from microlog import events
from microlog.stack import Call
from microlog.stack import CallSite
from microlog.stack import Stack


class StackTest(unittest.TestCase):
    def test_Call_eq(self):
        callSite1 = CallSite("example.py", 23, "f1")
        callSite2 = CallSite("example.py", 10, "f2")
        callSite3 = CallSite("example.py", 55, "f3")
        self.assertNotEqual(
            Call(0.1234, callSite1, callSite2, 3, 0),
            Call(0.2345, callSite2, callSite3, 5, 0)
        )
        self.assertEqual(
            Call(0.1234, callSite1, callSite2, 3, 0),
            Call(0.5678, callSite1, callSite2, 4, 0),
        )

    def test_CallSite_eq(self):
        self.assertNotEqual(
            CallSite("example.py", 23, "f1"),
            CallSite("example.py", 10, "f2")
        )
        self.assertNotEqual(
            CallSite("example.py", 5, "f1"),
            CallSite("example.py", 5, "f2")
        )
        self.assertEqual(
            CallSite("example.py", 7, "f1"), # only the name is relevant
            CallSite("example.py", 8, "f1")
        )
        self.assertEqual(
            CallSite("file1.py", 7, "f1"), # only the name is relevant
            CallSite("file2.py", 7, "f1")
        )
        self.assertEqual(
            CallSite("example.py", 10, "f1"),
            CallSite("example.py", 10, "f1")
        )

    def getCurrentFrame(self):
        return sys._current_frames()[threading.current_thread().ident]

    def test_Stack__getitem__(self):
        frame = self.getCurrentFrame()
        stack = Stack(0, frame)
        call = stack[-2]
        self.assertIsInstance(call, Call)
        self.assertTrue("StackTest" in call.callSite.name)

    def test_Stack__iter__(self):
        frame = self.getCurrentFrame()
        stack = Stack(startFrame=frame)
        copy = list(stack)  # this uses stack as an iterator
        self.assertEqual(len(stack), len(copy))

    def test_Stack__len__(self):
        frame = self.getCurrentFrame()
        stack1 = Stack(startFrame=frame)
        stack2 = Stack(startFrame=frame)
        stack3 = Stack()
        self.assertEqual(len(stack1), len(stack2))
        self.assertNotEqual(len(stack1), len(stack3))

    def test_callSiteFromFrame(self):
        frame = self.getCurrentFrame()
        stack = Stack()
        callSite = stack.callSiteFromFrame(frame, 13)
        self.assertEqual(callSite.lineno, 13)
        self.assertTrue("StackTest.getCurrentFrame" in callSite.name)
        self.assertTrue(callSite.filename.endswith("tracer.py"))

    def test_getCallSiteIndex(self):
        callSite1 = CallSite("example.py", 23, "f1")
        callSite2 = CallSite("example.py", 10, "f2")
        call1 = Call(0.1234, callSite1, callSite2, 3, 0)
        self.assertEqual(call1.getCallSiteIndex(), 0)
        call2 = Call(0.5678, callSite2, callSite1, 5, 0)
        self.assertEqual(call2.getCallSiteIndex(), 1)

    def test_ignore(self):
        frame = self.getCurrentFrame()
        stack = Stack()
        self.assertFalse(stack.ignore(frame))
        frame.f_globals["__name__"] = "microlog" # simulate call
        self.assertTrue(stack.ignore(frame))

    def test_save(self):
        events.clear()
        callSite1 = CallSite("example.py", 23, "f1")
        callSite2 = CallSite("example.py", 10, "f2")
        call1 = Call(0.1234, callSite1, callSite2, 3, 0)
        call2 = Call(0.5678, callSite2, callSite1, 7, 0)
        call1.save(0.1234, call2)
        event = events.get() 
        print(event)
        self.assertEqual(event[0], config.EVENT_KIND_SYMBOL)
        event = events.get() 
        print(event)
        self.assertEqual(event[0], config.EVENT_KIND_SYMBOL)
        event = events.get() 
        print(event)
        kind, callIndex1, callIndex2, depth, whenIndex, durationIndex = event
        self.assertEqual(kind, config.EVENT_KIND_CALL)
        self.assertEqual(callIndex1, 0)
        self.assertEqual(callIndex2, 1)
        self.assertEqual(depth, 3)
        self.assertEqual(symbols.get(whenIndex), 0.123)
        self.assertEqual(symbols.get(durationIndex), 0)

    def test_skip(self):
        frame = self.getCurrentFrame()
        stack = Stack()
        self.assertFalse(stack.skip(frame, 13))
        frame.f_globals["__name__"] = "microlog.stats" # simulate call
        self.assertTrue(stack.skip(frame, 27))


if __name__ == "__main__":
    unittest.main()