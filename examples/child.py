"""Child script for the parent example"""
import os
import time


# this script is run as a child process of parent.py

print("Child: Start")
print("Child: Parent ID=", os.environ.get("MICROLOG_PARENT_ID", "not set"))
print("Child: My own ID=", os.environ.get("MICROLOG_ID", "not set"))
time.sleep(2)
print("Child: End")
