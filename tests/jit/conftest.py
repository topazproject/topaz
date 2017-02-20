import os
import py
import sys


class JitTestUpdater(object):
    should_update = False

    def __init__(self, trace, expected_ops, exception):
        self.trace = trace
        self.expected_ops = expected_ops
        self.exception = exception

    def find_test_file(self):
        import traceback, re
        stk = traceback.extract_stack()
        stk.reverse()
        for filename, lineno, funcname, text in stk:
            if re.search("tests/jit/test_", filename):
                return filename, lineno
        return None, None

    def get_updated_contents(self, filename, lineno):
        lno = lineno - 10 # heuristic ;)
        with open(filename) as f:
            contents = f.readlines()
        newline = "\r\n" if contents[0].endswith("\r\n") else "\n"
        try:
            while contents[lno].strip() != str(self.expected_ops[0]).strip():
                lno += 1
        except IndexError:
            raise self.exception
        indent = (len(contents[lno]) - len(contents[lno].lstrip())) * " "
        contents[lno:lno + len(self.expected_ops)] = [
            (indent + str(op) + newline) for op in self.trace
        ]
        return contents

    def print_diff(self, trace_names, expected_names):
        import difflib
        output = (['Comparing Traces failed:'] +
                  ["-------OLD------"] +
                  [str(op) for op in self.expected_ops] +
                  ["-------NEW------"] +
                  [str(op) for op in self.trace] +
                  ["-------DIFF-----"] +
                  list(difflib.unified_diff(expected_names, trace_names)))
        print "\n".join(output)

    def ask_to_update_or_raise(self):
        if self.should_update:
            trace_names = [lop.name for lop in self.trace]
            expected_names = [rop.name for rop in self.expected_ops]
            self.print_diff(trace_names, expected_names)
            sys.stdout.write("Should we accept the new version (y/N)? ")
            if sys.stdin.readline().strip().upper() == "Y":
                filename, lineno = self.find_test_file()
                if not filename:
                    raise self.exception
                contents = self.get_updated_contents(filename, lineno)
                with open(filename, "w") as f:
                    f.truncate(0)
                    f.writelines(contents)
                return
        raise self.exception


def pytest_addoption(parser):
    group = parser.getgroup("Topaz JIT tests")
    group.addoption(
        "--topaz",
        dest="topaz",
        default=None,
        help="Path to a compiled topaz binary"
    )
    group.addoption(
        "--update", "-U",
        dest="update-jit-tests",
        action="store_true",
        default=False,
        help="Ask if we should update the JIT fixtures"
    )


def pytest_funcarg__topaz(request):
    global UPDATE_JIT_TESTS
    JitTestUpdater.should_update = request.config.getvalue("update-jit-tests")
    return py.path.local(request.config.getvalueorskip("topaz"))
