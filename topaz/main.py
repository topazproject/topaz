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
#   """  -rlibrary       require the library, before executing your script""",
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


def _entry_point(space, argv):
    try:
        ruby_main_opts = parse_command_line(space, argv[1:])
    except CommandLineError, e:
        print_error(str(e))
        return 1
    except SpaceSystemExit, e:
        return 0
    setup_load_path(space, ruby_main_opts.load_path_entries)
    return run_command_line(space, ruby_main_opts)


def version_info():
    system, _, _, _, cpu = os.uname()
    platform = "%s-%s" % (cpu, system.lower())
    engine = "topaz"
    version = "1.9.3"
    patchlevel = 125
    description = "%s (ruby-%sp%d) [%s]" % (engine, version, patchlevel, platform)
    return {
        "engine":      engine,
        "version":     version,
        "patchlevel":  str(patchlevel),
        "platform":    platform,
        "description": description,
    }


def handle_argument(c, options, iterargv, iterarg):
    function, has_funcarg, errmsg = ruby_main_opts_handlers[c]

    funcarg = ""
    if has_funcarg:
        remaining = []
        for arg in iterarg:
            remaining.append(arg)
        if len(remaining) > 0:
            funcarg = "".join(remaining)
        else:
            try:
                funcarg = iterargv.next()
            except StopIteration:
                if len(c) == 1:
                    c = '-' + c
                raise CommandLineError('%s %s (RuntimeError)' % (errmsg, c))

    return function(options, funcarg, iterargv)


class CommandLineError(Exception):
    pass


class SpaceSystemExit(Exception):
    pass


def print_help(*args):
    os.write(1, USAGE)
    raise SpaceSystemExit


def print_version(*args):
    os.write(1, "%s\n" % version_info()["description"])
    raise SpaceSystemExit


def print_error(msg):
    os.write(2, "topaz: %s\n" % msg)


def v_option(options, _, iterargv):
    options.verbose = True


def e_option(options, runcmd, iterargv):
    options.exprs.append(runcmd)


def I_option(options, load_path_option, iterargv):
    for entry in load_path_option.split(os.pathsep):
        options.load_path_entries.append(entry)


def end_options(options, _, iterargv):
    consumed = []
    for arg in iterargv:
        consumed.append(arg)
    return consumed


ruby_main_opts_handlers = {
    "v":         (v_option,      False, ""),
    "h":         (print_help,    False, ""),
    "--help":    (print_help,    False, ""),
    "e":         (e_option,      True,  "no code specified for"),
    "I":         (I_option,      True,  ""),
    "--version": (print_version, False, ""),
    "--":        (end_options,   False, ""),
}


class RubyMainOptions(object):
    def __init__(self):
        self.verbose = False
        self.exprs = []
        self.run_stdin = False
        self.load_path_entries = []
        self.ruby_argv = []


def parse_command_line(space, argv):
    options = RubyMainOptions()

    iterargv = iter(argv)
    argv = None
    for arg in iterargv:
        if len(arg) < 2 or arg[0] != '-':
            consumed = []
            for remaining in iterargv:
                consumed.append(remaining)
            argv = [arg] + consumed
        elif arg in ruby_main_opts_handlers:
            argv = handle_argument(arg, options, iterargv, iter(''))
        else:
            iterarg = iter(arg)
            iterarg.next()
            for c in iterarg:
                if c not in ruby_main_opts_handlers:
                    raise CommandLineError(
                        'invalid option -%s  (-h will show valid options) (RuntimeError)' % (c,)
                    )
                argv = handle_argument(c, options, iterargv, iterarg)

    if not argv:
        argv = ['']
        options.run_stdin = True
    elif argv[0] == '-':
        options.run_stdin = True

    options.ruby_argv = argv

    return options


def setup_load_path(space, load_path_entries):
    for path_entry in load_path_entries:
        space.send(
            space.w_load_path,
            space.newsymbol("<<"),
            [space.newstr_fromstr(path_entry)]
        )


def run_command_line(space, ruby_main_opts):
    source = ""

    vinfo = version_info()
    space.set_const(space.w_object, "RUBY_ENGINE", space.newstr_fromstr(vinfo["engine"]))
    space.set_const(space.w_object, "RUBY_VERSION", space.newstr_fromstr(vinfo["version"]))
    space.set_const(space.w_object, "RUBY_PATCHLEVEL", space.newint(int(vinfo["patchlevel"])))
    space.set_const(space.w_object, "RUBY_PLATFORM", space.newstr_fromstr(vinfo["platform"]))
    space.set_const(space.w_object, "RUBY_DESCRIPTION", space.newstr_fromstr(vinfo["description"]))

    if ruby_main_opts.verbose:
        os.write(1, "%s\n" % vinfo["description"])

    if ruby_main_opts.exprs:
        source = "\n".join(ruby_main_opts.exprs)
        path = "-e"
    elif ruby_main_opts.run_stdin:
        source = fdopen_as_stream(0, "r").readall()
        path = "-"
    else:
        path = ruby_main_opts.ruby_argv[0]
        ruby_main_opts.ruby_argv = ruby_main_opts.ruby_argv[1:]
        try:
            f = open_file_as_stream(path)
        except OSError as e:
            os.write(2, "%s -- %s (LoadError)\n" % (os.strerror(e.errno), path))
            return 1
        try:
            source = f.readall()
        finally:
            f.close()

    argv_w = space.newarray([])
    for arg in ruby_main_opts.ruby_argv:
        space.send(argv_w, space.newsymbol("<<"), [space.newstr_fromstr(arg)])
    space.set_const(space.w_object, "ARGV", argv_w)

    status = run_toplevel(space, path, source)
    return status


def run_toplevel(space, path, source):
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
