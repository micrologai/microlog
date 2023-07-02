#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import datetime
import os
import re
import sys
import time
import bz2

from microlog import config
from microlog.models import Call
from microlog.models import CallSite
from microlog.models import Status
from microlog.models import Marker

verbose = True

class Log():
    def __init__(self):
        self.start()

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

    def save(self):
        lines = []
        Call.save(reversed(self.calls), lines)
        Marker.save(reversed(self.markers), lines)
        Status.save(reversed(self.statuses), lines)
        return "\n".join(lines)

    def load(self, data: str):
        lines = data.split("\n")
        symbols = {}
        callSites = {}
        self.calls = []
        self.markers = []
        self.statuses = []
        for line in reversed(lines):
            kind = int(line[0])
            if kind == config.EVENT_KIND_SYMBOL:
                parts = line[2:].split()
                index = parts[0]
                symbol = " ".join(parts[1:])
                symbols[index] = symbol.replace("\\n", "\n")
            elif kind == config.EVENT_KIND_CALLSITE:
                index, callSite = CallSite.load(line, symbols)
                callSites[index] = callSite
            elif kind == config.EVENT_KIND_CALL:
                call = Call.load(line, callSites)
                self.calls.append(call)
            elif kind == config.EVENT_KIND_STATUS:
                self.statuses.append(Status.load(line))
            elif kind in [config.EVENT_KIND_DEBUG, config.EVENT_KIND_INFO,
                                config.EVENT_KIND_WARN, config.EVENT_KIND_ERROR]:
                self.markers.append(Marker.load(line, symbols))

    def stop(self):
        uncompressed = bytes(self.save(), encoding="utf-8")
        identifier = getIdentifier()
        path = getLogPath(identifier)
        with open(path.replace(".zip",""), "w") as fd:
            fd.write(self.save())
        with open(path, "wb") as fd:
            fd.write(bz2.compress(uncompressed, 9))
        if not verbose:
            return
        if "VSCODE_CWD" in os.environ and not "ipykernel" in sys.modules:
            return
        self.showDetails(path, identifier)
    
    def showDetails(self, path, identifier):
        application, version, _ = identifier.split("/")
        duration = self.now()
        sys.stdout.write("\n".join([
            "-" * 90,
            f"Microlog Statistics for {application}:",
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
