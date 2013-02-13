from __future__ import absolute_import

import os

from rpython.rlib.objectmodel import specialize
from rpython.rlib.streamio import open_file_as_stream, fdopen_as_stream

from topaz.error import RubyError, print_traceback
from topaz.objects.exceptionobject import W_SystemExit
from topaz.objspace import ObjectSpace


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
    load_path_entries = []
    idx = 1
    while idx < len(argv):
        arg = argv[idx]
        if arg == "-v":
            verbose = True
        elif arg == "-e":
            idx += 1
            if idx == len(argv):
                os.write(2, "no code specified for -e (RuntimeError)\n")
                return 1
            exprs.append(argv[idx])
        elif arg.startswith("-e"):
            exprs.append(arg[2:])
        elif arg == "-I":
            idx += 1
            load_path_entries += argv[idx].split(os.pathsep)
        elif arg.startswith("-I"):
            load_path_entries += arg[2:].split(os.pathsep)
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
    for path_entry in load_path_entries:
        space.send(
            space.w_load_path,
            space.newsymbol("<<"),
            [space.newstr_fromstr(path_entry)]
        )
    space.set_const(space.w_object, "ARGV", space.newarray(argv_w))

    system, _, _, _, cpu = os.uname()
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
        try:
            f = open_file_as_stream(path)
        except OSError as e:
            os.write(2, "%s -- %s (LoadError)\n" % (os.strerror(e.errno), path))
            return 1
        try:
            source = f.readall()
        finally:
            f.close()
    elif verbose:
        return 0
    else:
        source = fdopen_as_stream(0, "r").readall()
        path = "-"

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
