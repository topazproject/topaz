import subprocess

# TODO:
from pypy.tool.jitlogparser.parser import SimpleParser, Op
from pypy.tool.jitlogparser.storage import LoopStorage

from rpython.jit.metainterp.resoperation import opname
from rpython.jit.tool import oparser
from rpython.tool import logparser


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

    def assert_matches(self, trace, expected):
        expected_lines = [
            line.strip()
            for line in expected.splitlines()
            if line and not line.isspace()
        ]
        parser = Parser(None, None, {}, "lltype", None, invent_fail_descr=None, nonstrict=True)
        expected_ops = [parser.parse_next_op(l) for l in expected_lines]
        aliases = {}
        assert len(trace) == len(expected_ops)
        for op, expected in zip(trace, expected_ops):
            self._assert_ops_equal(aliases, op, expected)

    def _assert_ops_equal(self, aliases, op, expected):
        assert op.name == expected.name
        assert len(op.args) == len(expected.args)
        for arg, expected_arg in zip(op.args, expected.args):
            if arg in aliases:
                arg = aliases[arg]
            elif arg != expected_arg and expected_arg not in aliases.viewvalues():
                aliases[arg] = arg = expected_arg
            assert arg == expected_arg


class Parser(oparser.OpParser):
    def get_descr(self, poss_descr, allow_invent):
        if poss_descr.startswith(("TargetToken", "<Guard")):
            return poss_descr
        return super(Parser, self).get_descr(poss_descr, allow_invent)

    def getvar(self, arg):
        return arg

    def create_op(self, opnum, args, res, descr):
        return Op(opname[opnum].lower(), args, res, descr)


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
