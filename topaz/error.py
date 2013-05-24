import os
import errno


class RubyError(Exception):
    def __init__(self, w_value):
        self.w_value = w_value

    def __str__(self):
        return "<RubyError: %s>" % self.w_value


def format_traceback(space, exc, top_filepath):
    w_bt = space.send(exc, "backtrace")
    bt_w = space.listview(w_bt)
    if bt_w:
        yield "%s: %s (%s)\n" % (space.str_w(bt_w[0]), exc.msg, space.getclass(exc).name)
        for w_line in bt_w[1:]:
            yield "\tfrom %s\n" % space.str_w(w_line)
    else:
        yield "%s: %s (%s)\n" % (top_filepath, exc.msg, space.getclass(exc).name)


def print_traceback(space, w_exc, top_filepath=None):
    for line in format_traceback(space, w_exc, top_filepath):
        os.write(2, line)


def error_for_oserror(space, exc):
    return space.error(
        space.w_SystemCallError,
        os.strerror(exc.errno),
        [space.newint(exc.errno)]
    )

_errno_for_oserror_map = {
    errno.ECHILD: "ECHILD",
}

def errno_for_oserror(callee, space, exc):
    try:
        name = _errno_for_oserror_map[exc.errno]
    except KeyError:
        raise NotImplementedError("no such errno: %s" % exc.errno)
    return space.error(
        space.find_const(space.find_const(callee, "Errno"), name),
        os.strerror(exc.errno)
    )
