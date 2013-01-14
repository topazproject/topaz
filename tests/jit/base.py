import subprocess

from pypy.tool import logparser
from pypy.tool.jitlogparser.parser import SimpleParser
from pypy.tool.jitlogparser.storage import LoopStorage


class BaseJITTest(object):
    def run(self, topaz, tmpdir, code):
        tmpdir.join("t.rb").write(code)
        proc = subprocess.Popen(
            [str(topaz), str(tmpdir.join("t.rb"))],
            cwd=str(tmpdir),
            env={"PYPYLOG": "jit-log-opt:%s" % tmpdir.join("x.pypylog")}
        )
        proc.wait()
        data = logparser.parse_log_file(str(tmpdir.join("x.pypylog")), verbose=False)
        data = logparser.extract_category(data, "jit-log-opt-")

        storage = LoopStorage()
        traces = [SimpleParser.parse_from_input(t) for t in data]
        traces = storage.reconnect_loops(traces)
        return [Trace(t) for t in traces]

    def matches(self, trace, expected):
        expected_lines = [
            line.strip()
            for line in expected.splitlines()
            if line and not line.isspace()
        ]
        return map(str, trace) == expected_lines


class Trace(object):
    def __init__(self, trace):
        self.trace = trace

    @property
    def loop(self):
        label_seen = False
        for idx, op in enumerate(self.trace.operations):
            if op.name == "label":
                if label_seen:
                    return self.trace.operations[idx:]
                label_seen = True
        raise ValueError("Loop body couldn't be found")
