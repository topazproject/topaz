import subprocess
import re

from rpython.jit.metainterp.resoperation import opname
from rpython.jit.tool import oparser
from rpython.tool import logparser
from rpython.tool.jitlogparser.parser import SimpleParser, Op
from rpython.tool.jitlogparser.storage import LoopStorage

from .conftest import JitTestUpdater


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
        parser = Parser(None, None, {}, "lltype", invent_fail_descr=None, nonstrict=True)
        expected_ops = [parser.parse_next_op(l) for l in expected_lines]
        aliases = {}
        for op, expected in zip(trace, expected_ops):
            try:
                assert len(trace) == len(expected_ops)
                self._assert_ops_equal(aliases, op, expected)
            except Exception as e:
                JitTestUpdater(trace, expected_ops, e).ask_to_update_or_raise()

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

    def update_vector(self, resop, res):
        return res

    def getvar(self, arg):
        return arg

    def create_op(self, opnum, args, res, descr, fail_args):
        return Op(opname[opnum].lower(), args, res, descr)


class Trace(object):
    def __init__(self, trace):
        self.trace = self.strip_debug_paths(trace)

    def strip_debug_paths(self, trace):
        for op in trace.operations:
            if op.name == "debug_merge_point":
                # strip the file info in the debug_merge_points
                op.args[-1] = re.sub(r"[^'].*:in ", "", op.args[-1])
        return trace

    @property
    def loop(self):
        label_seen = False
        for idx, op in enumerate(self.trace.operations):
            if op.name == "label":
                if label_seen:
                    return self.trace.operations[idx:]
                label_seen = True
        raise ValueError("Loop body couldn't be found")
