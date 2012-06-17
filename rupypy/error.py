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
        frame.get_lineno(exc.last_instructions[last_instr_idx]),
        frame.get_code_name(),
        exc.msg,
        space.getclass(exc).name,
    ))
    last_instr_idx += 1
    frame = frame.backref()
    while frame is not None:
        lines.append("\tfrom %s:%d:in `%s'\n" % (
            frame.get_filename(),
            frame.get_lineno(exc.last_instructions[last_instr_idx]),
            frame.get_code_name(),
        ))
        last_instr_idx += 1
        frame = frame.backref()
    return lines
