from __future__ import absolute_import

import os

from rpython.rlib.objectmodel import specialize
from rpython.rlib.streamio import open_file_as_stream, fdopen_as_stream

from topaz.error import RubyError, print_traceback
from topaz.objects.exceptionobject import W_SystemExit
from topaz.objspace import ObjectSpace


USAGE = "\n".join([
    """Usage: topaz [switches] [--] [programfile] [arguments]""",
#   """  -0[octal]       specify record separator (\0, if no argument)""",
#   """  -a              autosplit mode with -n or -p (splits $_ into $F)""",
#   """  -c              check syntax only""",
#   """  -Cdirectory     cd to directory, before executing your script""",
#   """  -d              set debugging flags (set $DEBUG to true)""",
    """  -e 'command'    one line of script. Several -e's allowed. Omit [programfile]""",
#   """  -Eex[:in]       specify the default external and internal character encodings""",
#   """  -Fpattern       split() pattern for autosplit (-a)""",
#   """  -i[extension]   edit ARGV files in place (make backup if extension supplied)""",
    """  -Idirectory     specify $LOAD_PATH directory (may be used more than once)""",
#   """  -l              enable line ending processing""",
#   """  -n              assume 'while gets(); ... end' loop around your script""",
#   """  -p              assume loop like -n but print line also like sed""",
    """  -rlibrary       require the library, before executing your script""",
#   """  -s              enable some switch parsing for switches after script name""",
#   """  -S              look for the script using PATH environment variable""",
#   """  -T[level=1]     turn on tainting checks""",
    """  -v              print version number, then turn on verbose mode""",
#   """  -w              turn warnings on for your script""",
#   """  -W[level=2]     set warning level; 0=silence, 1=medium, 2=verbose""",
#   """  -x[directory]   strip off text before #!ruby line and perhaps cd to directory""",
#   """  --copyright     print the copyright""",
    """  --version       print the version""",
    ""
])


@specialize.memo()
def getspace():
    return ObjectSpace()


def entry_point(argv):
    space = getspace()
    space.setup(argv[0])
    return _entry_point(space, argv)


class CommandLineError(Exception):
    def __init__(self, message):
        self.message = message


class ShortCircuitError(Exception):
    def __init__(self, message):
        self.message = message


def _parse_argv(space, argv):
    verbose = False
    path = None
    exprs = []
    reqs = []
    load_path_entries = []
    argv_w = []
    idx = 1
    while idx < len(argv):
        arg = argv[idx]
        if arg == "-h" or arg == "--help":
            raise ShortCircuitError(USAGE)
        elif arg == "--version":
            raise ShortCircuitError("%s\n" % space.str_w(
                    space.send(
                        space.w_object,
                        space.newsymbol("const_get"),
                        [space.newstr_fromstr("RUBY_DESCRIPTION")]
                    )
                ))
        elif arg == "-v":
            verbose = True
        elif arg == "-e":
            idx += 1
            if idx == len(argv):
                raise CommandLineError("no code specified for -e (RuntimeError)\n")
            exprs.append(argv[idx])
        elif arg.startswith("-e"):
            exprs.append(arg[2:])
        elif arg == "-I":
            idx += 1
            load_path_entries += argv[idx].split(os.pathsep)
        elif arg.startswith("-I"):
            load_path_entries += arg[2:].split(os.pathsep)
        elif arg == "-r":
            idx += 1
            reqs.append(argv[idx])
        elif arg.startswith("-r"):
            reqs.append(arg[2:])
        elif arg == "--":
            idx += 1
            break
        else:
            break
        idx += 1
    if idx < len(argv) and not exprs:
        path = argv[idx]
        idx += 1
    while idx < len(argv):
        argv_w.append(space.newstr_fromstr(argv[idx]))
        idx += 1

    return verbose, path, exprs, reqs, load_path_entries, argv_w


def _entry_point(space, argv):
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

    try:
        verbose, path, exprs, reqs, load_path_entries, argv_w = _parse_argv(space, argv)
    except ShortCircuitError as e:
        os.write(1, e.message)
        return 0
    except CommandLineError as e:
        os.write(2, e.message)
        return 1

    for path_entry in load_path_entries:
        space.send(
            space.w_load_path,
            space.newsymbol("<<"),
            [space.newstr_fromstr(path_entry)]
        )
    for required_lib in reqs:
        space.send(
            space.w_kernel,
            space.newsymbol("require"),
            [space.newstr_fromstr(required_lib)]
        )

    space.set_const(space.w_object, "ARGV", space.newarray(argv_w))

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
