import os

from rupypy.objects.exceptionobject import W_SystemCallError


class RubyError(Exception):
    def __init__(self, w_value):
        self.w_value = w_value

    def __str__(self):
        return "<RubyError: %s>" % self.w_value


def format_traceback(space, exc):
    lines = []
    last_instr_idx = 0
    frame = exc.frame
    lines.append("%s:%d:in `%s': %s (%s)\n" % (
        frame.get_filename(),
        frame.get_lineno(exc.last_instructions, last_instr_idx),
        frame.get_code_name(),
        exc.msg,
        space.getclass(exc).name,
    ))
    last_instr_idx += 1
    frame = frame.backref()
    while frame is not None and frame.has_contents():
        lines.append("\tfrom %s:%d:in `%s'\n" % (
            frame.get_filename(),
            frame.get_lineno(exc.last_instructions, last_instr_idx),
            frame.get_code_name(),
        ))
        last_instr_idx += 1
        frame = frame.backref()
    return lines


def print_traceback(space, w_exc):
    for line in format_traceback(space, w_exc):
        os.write(2, line)


def error_for_oserror(space, exc):
    assert isinstance(exc, OSError)
    return space.error(
        space.getclassfor(W_SystemCallError),
        os.strerror(exc.errno),
        [space.newint(exc.errno)]
    )
