#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import datetime
import os
import json
import re
import sys
import time
import zlib

from microlog.models import Call
from microlog.models import Status
from microlog.models import Marker

verbose = True

class Log():
    def __init__(self):
        self.start()

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def start(self):
        self.calls = []
        self.markers = []
        self.statuses = []
        self.begin = time.perf_counter()

    def now(self):
        return time.perf_counter() - self.begin

    def addCall(self, call: Call):
        self.calls.append(call)

    def addStatus(self, status: Status):
        self.statuses.append(status)

    def addMarker(self, marker: Marker):
        self.markers.append(marker)

    def load(self, data):
        other = json.loads(data)
        self.calls = other["calls"]
        self.statuses = other["statuses"]
        self.markers = other["markers"]

    def stop(self):
        duration = self.now()
        uncompressed = bytes(self.toJson(), encoding="utf-8")
        identifier = getIdentifier()
        path = getLogPath(identifier)
        with open(path, "wb") as fd:
            fd.write(zlib.compress(uncompressed, level=9))
        if verbose:
            if not "VSCODE_CWD" in os.environ:
                sys.stdout.write("\n".join([
                    "-" * 90,
                    "Microlog Statistics:",
                    "-" * 90,
                    f"- log size:    {os.stat(path).st_size:,} bytes",
                    f"- report URL:  {f'http://127.0.0.1:4000/log/{identifier}'}",
                    f"- duration:    {duration:.3f}s",
                    "-" * 90,
                    ""
                ]))

log = Log()


def start():
    log.start()


def sanitize(filename):
    return filename.replace("/", "_")


def getApplication():
    from microlog import config
    if config.application:
         return config.application
    name = sys.argv[0] if sys.argv[0] != "-c" else "python"
    name = "-".join(name.split("/")[-3:])
    name = name.replace("python-site-packages-", "").replace(".py", "")
    name = name.replace(os.path.expanduser("~"), "~")
    return name


def getVersion():
    from microlog import config
    if config.version:
         return config.version
    path = os.path.abspath(sys.argv[0])
    while path != "/":
        setup = os.path.join(path, "setup.py")
        if os.path.exists(setup):
            import ast
            tree = ast.parse(open(setup).read())
            for line in ast.dump(tree, indent=4).split("\n"):
                if re.search("value='[0-9.]*'", line):
                    return re.sub(r".*value='([0-9.]*)'.*", r"\1", line)
        path = os.path.dirname(path)
    return "0.0.0"


def getEnvironment():
    return "dev"


def getIdentifier():
    date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return f"{getApplication()}/{getVersion()}/{date}"


def getLogPath(identifier):
    import appdata
    paths = appdata.AppDataPaths('microlog')
    if paths.require_setup:
        paths.setup()
    path = paths.get_log_file_path(identifier)
    dirname = os.path.dirname(path)
    os.makedirs(dirname, exist_ok=True)
    return f"{path}.zip"
