from __future__ import absolute_import

import os
import subprocess

from rpython.rlib import jit
from rpython.rlib.objectmodel import specialize
from rpython.rlib.streamio import open_file_as_stream, fdopen_as_stream

from topaz.error import RubyError, print_traceback
from topaz.objects.exceptionobject import W_SystemExit
from topaz.objspace import ObjectSpace
from topaz.system import IS_WINDOWS, IS_64BIT


USAGE = "\n".join([
    """Usage: topaz [switches] [--] [programfile] [arguments]""",
    # """  -0[octal]       specify record separator (\0, if no argument)""",
    # """  -a              autosplit mode with -n or -p (splits $_ into $F)""",
    # """  -c              check syntax only""",
    # """  -Cdirectory     cd to directory, before executing your script""",
    """  -d              set debugging flags (set $DEBUG to true)""",
    """  -e 'command'    one line of script. Several -e's allowed. Omit [programfile]""",
    # """  -Eex[:in]       specify the default external and internal character encodings""",
    # """  -Fpattern       split() pattern for autosplit (-a)""",
    # """  -i[extension]   edit ARGV files in place (make backup if extension supplied)""",
    """  -Idirectory     specify $LOAD_PATH directory (may be used more than once)""",
    # """  -l              enable line ending processing""",
    """  -n              assume 'while gets(); ... end' loop around your script""",
    """  -p              assume loop like -n but print line also like sed""",
    """  -rlibrary       require the library, before executing your script""",
    """  -s              enable some switch parsing for switches after script name""",
    """  -S              look for the script using PATH environment variable""",
    # """  -T[level=1]     turn on tainting checks""",
    """  -v              print version number, then turn on verbose mode""",
    """  -w              turn warnings on for your script""",
    """  -W[level=2]     set warning level; 0=silence, 1=medium, 2=verbose""",
    # """  -x[directory]   strip off text before #!ruby line and perhaps cd to directory""",
    """  --copyright     print the copyright""",
    """  --version       print the version""",
    ""
])
COPYRIGHT = "topaz - Copyright (c) Alex Gaynor and individual contributors\n"
RUBY_REVISION = subprocess.check_output([
    "git",
    "--git-dir", os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, ".git"),
    "rev-parse", "--short", "HEAD"
]).rstrip()


@specialize.memo()
def getspace(config):
    return ObjectSpace(config)


def get_topaz_config_options():
    return {
        "translation.continuation": True,
    }


def create_entry_point(config):
    def entry_point(argv):
        space = getspace(config)
        space.setup(argv[0])
        return _entry_point(space, argv)
    return entry_point


class CommandLineError(Exception):
    def __init__(self, message):
        self.message = message


class ShortCircuitError(Exception):
    def __init__(self, message):
        self.message = message


def _parse_argv(space, argv):
    flag_globals_w = {
        "$-v": space.w_false,
        "$VERBOSE": space.w_false,
        "$-d": space.w_false,
        "$DEBUG": space.w_false,
        "$-w": space.w_false,
        "$-W": space.newint(1),
        "$-p": space.w_false,
        "$-l": space.w_false,
        "$-a": space.w_false,
    }
    warning_level = None
    do_loop = False
    path = None
    search_path = False
    globalize_switches = False
    globalized_switches = []
    exprs = []
    reqs = []
    load_path_entries = []
    argv_w = []
    idx = 1
    while idx < len(argv):
        arg = argv[idx]
        if arg == "-h" or arg == "--help":
            raise ShortCircuitError(USAGE)
        elif arg == "--copyright":
            raise ShortCircuitError(COPYRIGHT)
        elif arg == "--version":
            raise ShortCircuitError("%s\n" % space.str_w(
                space.send(
                    space.w_object,
                    "const_get",
                    [space.newstr_fromstr("RUBY_DESCRIPTION")]
                )
            ))
        elif arg == "-v":
            flag_globals_w["$-v"] = space.w_true
            flag_globals_w["$VERBOSE"] = space.w_true
        elif arg == "-d":
            flag_globals_w["$-d"] = space.w_true
            flag_globals_w["$VERBOSE"] = space.w_true
            flag_globals_w["$DEBUG"] = space.w_true
        elif arg == "-w":
            flag_globals_w["$-w"] = space.w_true
            flag_globals_w["$VERBOSE"] = space.w_true
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
        elif arg.startswith("-W"):
            warning_level = arg[2:]
        elif arg == "-S":
            search_path = True
        elif arg == "-s":
            globalize_switches = True
        elif arg == "-n":
            do_loop = True
        elif arg == "-p":
            do_loop = True
            flag_globals_w["$-p"] = space.w_true
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
        arg = argv[idx]
        if globalize_switches and arg.startswith("-"):
            globalized_switches.append(arg)
        else:
            argv_w.append(space.newstr_fromstr(arg))
        idx += 1

    if warning_level is not None:
        warning_level_num = 2 if not warning_level.isdigit() else int(warning_level)
        if warning_level_num == 0:
            flag_globals_w["$VERBOSE"] = space.w_nil
        elif warning_level_num == 1:
            flag_globals_w["$VERBOSE"] = space.w_false
        elif warning_level_num >= 2:
            flag_globals_w["$VERBOSE"] = space.w_true

        flag_globals_w["$-W"] = space.newint(warning_level_num)

    return (
        flag_globals_w,
        do_loop,
        path,
        search_path,
        globalized_switches,
        exprs,
        reqs,
        load_path_entries,
        argv_w
    )


def _entry_point(space, argv):
    if IS_WINDOWS:
        system = "Windows"
        cpu = "x86_64" if IS_64BIT else "i686"
    else:
        system, _, _, _, cpu = os.uname()
    platform = "%s-%s" % (cpu, system.lower())
    engine = "topaz"
    version = "1.9.3"
    patchlevel = 125
    description = "%s (ruby-%sp%d) (git rev %s) [%s]" % (engine, version, patchlevel, RUBY_REVISION, platform)
    space.set_const(space.w_object, "RUBY_ENGINE", space.newstr_fromstr(engine))
    space.set_const(space.w_object, "RUBY_VERSION", space.newstr_fromstr(version))
    space.set_const(space.w_object, "RUBY_PATCHLEVEL", space.newint(patchlevel))
    space.set_const(space.w_object, "RUBY_PLATFORM", space.newstr_fromstr(platform))
    space.set_const(space.w_object, "RUBY_DESCRIPTION", space.newstr_fromstr(description))
    space.set_const(space.w_object, "RUBY_REVISION", space.newstr_fromstr(RUBY_REVISION))

    try:
        (
            flag_globals_w,
            do_loop,
            path,
            search_path,
            globalized_switches,
            exprs,
            reqs,
            load_path_entries,
            argv_w
        ) = _parse_argv(space, argv)
    except ShortCircuitError as e:
        os.write(1, e.message)
        return 0
    except CommandLineError as e:
        os.write(2, e.message)
        return 1

    for path_entry in load_path_entries:
        space.send(
            space.w_load_path,
            "<<",
            [space.newstr_fromstr(path_entry)]
        )
    for required_lib in reqs:
        space.send(
            space.w_kernel,
            "require",
            [space.newstr_fromstr(required_lib)]
        )

    space.set_const(space.w_object, "ARGV", space.newarray(argv_w))
    explicitly_verbose = space.is_true(flag_globals_w["$-v"])
    if explicitly_verbose:
        os.write(1, "%s\n" % description)
    for varname, w_value in flag_globals_w.iteritems():
        space.globals.set(space, varname, w_value)

    if exprs:
        source = "\n".join(exprs)
        path = "-e"
    elif path is not None:
        if search_path:
            for dirname in os.environ["PATH"].split(os.pathsep):
                candidate_path = os.sep.join([dirname, path])
                if os.access(candidate_path, os.R_OK):
                    path = candidate_path
                    break
        try:
            f = open_file_as_stream(path, buffering=0)
        except OSError as e:
            os.write(2, "%s -- %s (LoadError)\n" % (os.strerror(e.errno), path))
            return 1
        try:
            source = f.readall()
        finally:
            f.close()
    elif explicitly_verbose:
        return 0
    else:
        if IS_WINDOWS:
            raise NotImplementedError("executing from stdin on Windows")
        else:
            source = fdopen_as_stream(0, "r").readall()
            path = "-"

    for globalized_switch in globalized_switches:
        value = None
        if "=" in globalized_switch:
            globalized_switch, value = globalized_switch.split("=", 1)

        switch_global_var = "$%s" % globalized_switch[1:].replace("-", "_")
        if value is None:
            space.globals.set(space, switch_global_var, space.w_true)
        else:
            space.globals.set(space, switch_global_var, space.newstr_fromstr(value))

    w_program_name = space.newstr_fromstr(path)
    space.globals.set(space, "$0", w_program_name)
    space.globals.set(space, "$PROGRAM_NAME", w_program_name)
    status = 0
    w_exit_error = None
    explicit_status = False
    jit.set_param(None, "trace_limit", 10000)
    try:
        if do_loop:
            print_after = space.is_true(flag_globals_w["$-p"])
            bc = space.compile(source, path)
            frame = space.create_frame(bc)
            while True:
                w_line = space.send(space.w_kernel, "gets")
                if w_line is space.w_nil:
                    break
                with space.getexecutioncontext().visit_frame(frame):
                    w_res = space.execute_frame(frame, bc)
                    if print_after:
                        space.send(space.w_kernel, "print", [w_res])
        else:
            space.execute(source, filepath=path)
    except RubyError as e:
        explicit_status = True
        w_exc = e.w_value
        if isinstance(w_exc, W_SystemExit):
            status = w_exc.status
        else:
            w_exit_error = w_exc
            status = 1
    exit_handler_status = space.run_exit_handlers()
    if not explicit_status and exit_handler_status != -1:
        status = exit_handler_status
    if w_exit_error is not None:
        print_traceback(space, w_exit_error, path)

    return status
