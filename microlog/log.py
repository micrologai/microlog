#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict
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

    def saveSymbols(self, lines, symbols):
        for symbol, _ in sorted(symbols.items(), key = lambda item: item[1]):
            lines.append(symbol.replace("\n", "\\n"))
        lines.append(f"{config.EVENT_KIND_SECTION} {config.EVENT_KIND_SYMBOL} {len(symbols)} SYMBOL")

    def save(self):
        lines = []
        symbols = defaultdict(lambda: len(symbols))
        Call.save(reversed(self.calls), lines, symbols)
        Marker.save(reversed(self.markers), lines, symbols)
        Status.save(reversed(self.statuses), lines, symbols)
        self.saveSymbols(lines, symbols)
        return "\n".join(reversed(lines))

    def load(self, data: str):
        lines = data.split("\n")
        symbols = {}
        symbolIndex = -1
        callSites = {}
        self.calls = []
        self.markers = []
        self.statuses = []
        kind = None
        for line in lines:
            if symbolIndex == -1 and line[0] == config.EVENT_KIND_SECTION:
                parts = line.split()
                kind = int(parts[1])
                if kind == config.EVENT_KIND_SYMBOL:
                    symbolIndex = int(parts[2]) - 1
            elif kind == config.EVENT_KIND_SYMBOL:
                symbols[symbolIndex] = line.replace("\\n", "\n")
                symbolIndex -= 1
            elif kind == config.EVENT_KIND_CALLSITE:
                index, callSite = CallSite.load(line, symbols)
                callSites[index] = callSite
            elif kind == config.EVENT_KIND_CALL:
                call = Call.load(line, callSites)
                self.calls.append(call)
            elif kind == config.EVENT_KIND_STATUS:
                self.statuses.append(Status.load(line, symbols))
            elif kind == config.EVENT_KIND_MARKER:
                self.markers.append(Marker.load(line, symbols))

    def stop(self):
        uncompressed = bytes(self.save(), encoding="utf-8")
        identifier = getIdentifier()
        path = getLogPath(identifier)
        with open(path.replace(".zip",""), "w") as fd:
            fd.write(self.save())
        sys.stdout.write(f'{path.replace(".zip", "")}\n')
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
            with open(setup) as fd:
                tree = ast.parse(fd.read())
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
