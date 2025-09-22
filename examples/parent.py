"""Example that shows how to start a child Microlog from a parent"""

import os
import time


print("Parent: Start")
print("Parent: Parent ID=", os.environ.get("MICROLOG_PARENT_ID", "not set"))
print("Parent: My own ID=", os.environ.get("MICROLOG_ID", "not set"))

time.sleep(2)

print("Creating child")
os.system("uv run -m microlog 'microlog-example-child' examples/child.py")
print("Child: End")
