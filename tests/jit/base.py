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
        return traces

    def matches(self, trace, expected):
        pass
