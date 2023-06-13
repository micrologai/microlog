#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import datetime
import json
import os
import re
import sys
import time
import zlib


begin = time.perf_counter()
buffer = []
verbose = True


def start():
    global begin
    begin = time.perf_counter()


def now():
    return time.perf_counter() - begin


def put(event):
    from microlog import config
    buffer.append(event)


def clear():
    buffer.clear()


def sanitize(filename):
    return filename.replace("/", "_")


def getApplication():
    name = sys.argv[0] if sys.argv[0] != "-c" else "python"
    return "-".join(name.split("/")[-3:]).replace("python-site-packages-", "").replace(".py", "")


def getVersion():
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


def validate():
    from microlog import config
    from microlog import models
    for n, event in enumerate(buffer):
        try:
            line = f'{",".join(json.dumps(e) for e in event)}'
            event = json.loads(f"[{line}]")
            kind = event[0]
            if kind == config.EVENT_KIND_SYMBOL:
                models.unmarshallSymbol(event)
            elif kind == config.EVENT_KIND_CALLSITE:
                models.CallSite.unmarshall(event)
            elif kind == config.EVENT_KIND_CALL:
                models.Call.unmarshall(event)
            elif kind == config.EVENT_KIND_META:
                models.Meta.unmarshall(event)
            elif kind == config.EVENT_KIND_STATUS:
                models.Status.unmarshall(event)
            elif kind in [ config.EVENT_KIND_INFO, config.EVENT_KIND_WARN, config.EVENT_KIND_DEBUG, config.EVENT_KIND_ERROR, ]:
                models.MarkerModel.unmarshall(event)
        except Exception as e:
            sys.stderr.write(f"Microlog: Error validating line {n+1} {e}:\n{line}\n")
            raise


def stop():
    from microlog import config
    uncompressed = bytes("\n".join(f'{",".join(json.dumps(e) for e in event)}' for event in buffer), encoding="utf-8")
    identifier = getIdentifier()
    path = getLogPath(identifier)
    with open(path, "wb") as fd:
        fd.write(zlib.compress(uncompressed, level=9))
    if verbose:
        duration = time.perf_counter() - begin
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
    buffer.clear()
