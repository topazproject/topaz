from __future__ import absolute_import

import os
import sys

from pypy.rlib.objectmodel import specialize
from pypy.rlib.streamio import open_file_as_stream

from rupypy.error import RubyError, format_traceback
from rupypy.objects.objectobject import W_Object
from rupypy.objects.exceptionobject import W_SystemExit
from rupypy.objspace import ObjectSpace


@specialize.memo()
def getspace():
    return ObjectSpace()


def entry_point(argv):
    space = getspace()

    verbose = False
    path = None
    argv_w = []
    idx = 1
    while idx < len(argv):
        arg = argv[idx]
        idx += 1
        if arg == "-v":
            verbose = True
        else:
            path = arg
            while idx < len(argv):
                arg = argv[idx]
                idx += 1
                argv_w.append(space.newstr_fromstr(arg))
    space.set_const(space.getclassfor(W_Object), "ARGV", space.newarray(argv_w))

    system, _, _, _, cpu = os.uname()
    platform = "%s-%s" % (cpu, system.lower())
    engine = "topaz"
    version = "1.9.3"
    patchlevel = 125
    description = "%s (ruby-%sp%d) [%s]" % (engine, version, patchlevel, platform)
    space.set_const(space.getclassfor(W_Object), "RUBY_ENGINE", space.newstr_fromstr(engine))
    space.set_const(space.getclassfor(W_Object), "RUBY_VERSION", space.newstr_fromstr(version))
    space.set_const(space.getclassfor(W_Object), "RUBY_PATCHLEVEL", space.newint(patchlevel))
    space.set_const(space.getclassfor(W_Object), "RUBY_PLATFORM", space.newstr_fromstr(platform))
    space.set_const(space.getclassfor(W_Object), "RUBY_DESCRIPTION", space.newstr_fromstr(platform))

    if verbose:
        os.write(1, "%s\n" % description)
    if path is not None:
        f = open_file_as_stream(path)
        try:
            source = f.readall()
        finally:
            f.close()

        try:
            space.execute(source, filepath=path)
        except RubyError as e:
            w_exc = e.w_value
            if isinstance(w_exc, W_SystemExit):
                space.run_exit_handlers()
                return w_exc.status
            else:
                lines = format_traceback(space, w_exc)
                for line in lines:
                    os.write(2, line)
                return 1
    return 0

if __name__ == "__main__":
    entry_point(sys.argv)
