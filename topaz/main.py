from __future__ import absolute_import

import os

from rpython.rlib.rarithmetic import is_emulated_long
from rpython.rlib.objectmodel import specialize
from rpython.translator.platform import platform as rpython_platform

from topaz.error import RubyError, print_traceback
from topaz.objects.exceptionobject import W_SystemExit
from topaz.objspace import ObjectSpace


if rpython_platform.name in ["msvc", "mingw32"]:
    system = "Windows"
    cpu = "x86_64" if is_emulated_long else "i686"
else:
    system, _, _, _, cpu = os.uname()


@specialize.memo()
def getspace():
    return ObjectSpace()


def entry_point(argv):
    space = getspace()
    space.setup(argv[0])
    return _entry_point(space, argv)


def _entry_point(space, argv):
    verbose = False
    path = None
    exprs = []
    idx = 1
    while idx < len(argv):
        arg = argv[idx]
        if arg == "-v":
            verbose = True
        elif arg == "-e":
            idx += 1
            exprs.append(argv[idx])
        else:
            break
        idx += 1
    if idx < len(argv) and not exprs:
        path = argv[idx]
        idx += 1
    argv_w = []
    while idx < len(argv):
        argv_w.append(space.newstr_fromstr(argv[idx]))
        idx += 1
    space.set_const(space.w_object, "ARGV", space.newarray(argv_w))

    platform = "%s-%s" % (cpu, system.lower())
    engine = "topaz"
    version = "1.9.3"
    patchlevel = 125
    description = "%s (ruby-%sp%d) [%s]" % (engine, version, patchlevel, platform)
    space.set_const(space.w_object, "RUBY_ENGINE", space.newstr_fromstr(engine))
    space.set_const(space.w_object, "RUBY_VERSION", space.newstr_fromstr(version))
    space.set_const(space.w_object, "RUBY_PATCHLEVEL", space.newint(patchlevel))
    space.set_const(space.w_object, "RUBY_PLATFORM", space.newstr_fromstr(platform))
    space.set_const(space.w_object, "RUBY_DESCRIPTION", space.newstr_fromstr(description))

    if verbose:
        os.write(1, "%s\n" % description)

    if exprs:
        source = "\n".join(exprs)
        path = "-e"
    elif path is not None:
        fd = -1
        try:
            fd = os.open(path, os.O_RDONLY, 0665)
            content_bytes = []
            while True:
                current_read = os.read(fd, 8192)
                if len(current_read) == 0:
                    break
                content_bytes += current_read
            source = "".join(content_bytes)
        finally:
            if fd > 2:
                os.close(fd)
    elif verbose:
        return 0
    else:
        raise NotImplementedError("reading script from stdin")

    space.globals.set(space, "$0", space.newstr_fromstr(path))
    status = 0
    w_exit_error = None
    try:
        space.execute(source, filepath=path)
    except RubyError as e:
        w_exc = e.w_value
        if isinstance(w_exc, W_SystemExit):
            status = w_exc.status
        else:
            w_exit_error = w_exc
            status = 1
    space.run_exit_handlers()
    if w_exit_error is not None:
        print_traceback(space, w_exit_error, path)

    return status
