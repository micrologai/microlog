#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict
import datetime
import os
import sys
import time
import bz2

from microlog import config
from microlog.models import Call
from microlog.models import CallSite
from microlog.models import Stack
from microlog.models import Status
from microlog.models import toGB
from microlog.models import Marker

verbose = True
debug = True

class Log():
    def __init__(self):
        self.start()

    def start(self):
        self.running = True
        self.calls = []
        self.markers = []
        self.statuses = []
        self.begin = time.perf_counter()

    def now(self):
        return time.perf_counter() - self.begin

    def addCall(self, call: Call):
        if not self.running: 
            return
        self.calls.append(call)

    def addStatus(self, status: Status):
        self.statuses.append(status)

    def addMarker(self, marker: Marker):
        self.markers.append(marker)

    def saveSymbols(self, lines, symbols):
        for symbol, _ in sorted(symbols.items(), key = lambda item: item[1]):
            lines.append(symbol.replace("\n", "\\n"))
        lines.append(f"{config.EVENT_KIND_SECTION} {config.EVENT_KIND_SYMBOL} {len(symbols)} Symbols")

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
        stacks = {}
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
                callSites[int(index)] = callSite
            elif kind == config.EVENT_KIND_STACK:
                stack = Stack.load(line, callSites)
                stacks[stack.index] = stack
            elif kind == config.EVENT_KIND_CALL:
                self.calls.append(Call.load(line, callSites))
            elif kind == config.EVENT_KIND_STATUS:
                self.statuses.append(Status.load(line, symbols))
            elif kind == config.EVENT_KIND_MARKER:
                self.markers.append(Marker.load(line, symbols, stacks))

    def stop(self):
        self.running = False
        if not getApplication():
            return
        uncompressed = bytes(self.save(), encoding="utf-8")
        identifier = getIdentifier()
        path = getLogPath(identifier)
        if debug:
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
        application, _ = identifier.split("/")
        duration = self.now()
        sys.stdout.write(f"📈 Microlog ··· {duration:.1f}s ··· {toGB(os.stat(path).st_size)} ··· {application} ··· {f'http://127.0.0.1:4000/log/{identifier}'} 🚀\n")

log = Log()


def start():
    log.start()


def sanitize(filename):
    return filename.replace("/", "_")


def getApplication():
    from microlog import config
    if config.application:
         return config.application
    name = sys.argv[0] if sys.argv[0] != "-c" else sys.argv[1] if sys.argv[0] == "-m" else "python"
    name = "-".join(name.split("/")[-3:])
    name = name.replace("python-site-packages-", "").replace(".py", "")
    return name

def getIdentifier():
    date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return f"{getApplication()}/{date}"


def getLogPath(identifier):
    import appdata
    paths = appdata.AppDataPaths('microlog')
    if paths.require_setup:
        paths.setup()
    path = paths.get_log_file_path(identifier)
    dirname = os.path.dirname(path)
    os.makedirs(dirname, exist_ok=True)
    return f"{path}.zip"
