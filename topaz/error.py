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


_errno_for_oserror_map = {
    errno.ECHILD: "ECHILD",
}

def error_for_oserror(space, exc, callee=None):
    if callee:
        try:
            name = _errno_for_oserror_map[exc.errno]
            type = space.find_const(space.find_const(callee, "Errno"), name)
        except KeyError:
            type = space.w_SystemCallError
    else:
        type = space.w_SystemCallError
    return space.error(
        type,
        os.strerror(exc.errno),
        [space.newint(exc.errno)]
    )
