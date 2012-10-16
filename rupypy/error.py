import os


class RubyError(Exception):
    def __init__(self, w_value):
        self.w_value = w_value

    def __str__(self):
        return "<RubyError: %s>" % self.w_value


def format_traceback(space, exc):
    w_ary = space.send(exc, space.newsymbol("backtrace"))
    assert space.getclass(w_ary) is space.w_array
    ary = space.listview(w_ary)
    yield "%s: %s (%s)\n" % (space.str_w(ary[0]), exc.msg, space.getclass(exc).name)
    for w_line in ary[1:]:
        yield "\tfrom %s\n" % space.str_w(w_line)


def print_traceback(space, w_exc):
    for line in format_traceback(space, w_exc):
        os.write(2, line)


def error_for_oserror(space, exc):
    assert isinstance(exc, OSError)
    return space.error(
        space.w_SystemCallError,
        os.strerror(exc.errno),
        [space.newint(exc.errno)]
    )
