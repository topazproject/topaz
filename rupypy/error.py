import os


class RubyError(Exception):
    def __init__(self, w_value):
        self.w_value = w_value

    def __str__(self):
        return "<RubyError: %s>" % self.w_value


def format_traceback(space, exc):
    w_bt = space.send(exc, space.newsymbol("backtrace"))
    assert space.getclass(w_bt) is space.w_array
    bt_w = space.listview(w_bt)
    yield "%s: %s (%s)\n" % (space.str_w(bt_w[0]), exc.msg, space.getclass(exc).name)
    for w_line in bt_w[1:]:
        yield "\tfrom %s\n" % space.str_w(w_line)


def print_traceback(space, w_exc):
    for line in format_traceback(space, w_exc):
        os.write(2, line)


def error_for_oserror(space, exc):
    return space.error(
        space.w_SystemCallError,
        os.strerror(exc.errno),
        [space.newint(exc.errno)]
    )
