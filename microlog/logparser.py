import json
import sys

import microlog.stack as stack
import microlog.symbols as symbols
import microlog.config as config
import microlog.meta as meta
import microlog.threads.status as status
import microlog.marker as marker


def parse(log):
    lines = [json.loads(f"[{line}]") for line in log.split("\n") if line]
    for lineno, event in enumerate(lines):
        kind = event[0]
        try:
            if kind == config.EVENT_KIND_SYMBOL:
                print(lineno, config.kinds[kind], symbols.unmarshall(event))
            elif kind == config.EVENT_KIND_CALLSITE:
                print(lineno, config.kinds[kind], stack.CallSite.unmarshall(event))
            elif kind == config.EVENT_KIND_CALL:
                print(lineno, config.kinds[kind], stack.Call.unmarshall(event))
            elif kind == config.EVENT_KIND_META:
                print(lineno, config.kinds[kind], meta.Meta.unmarshall(event))
            elif kind == config.EVENT_KIND_STATUS:
                print(lineno, config.kinds[kind], status.Status.unmarshall(event))
            elif kind in [ config.EVENT_KIND_INFO, config.EVENT_KIND_WARN, config.EVENT_KIND_DEBUG, config.EVENT_KIND_ERROR, ]:
                print(lineno, config.kinds[kind], marker.Marker.unmarshall(event))
        except:
            raise ValueError(f"Error on line {lineno}, kind={config.kinds[kind]}, event='{event}'")


def main():
    parse(open(sys.argv[1]).read())

main()
