from __future__ import absolute_import

from rpython.rlib import rsignal

from topaz.module import ModuleDef
from topaz.system import IS_WINDOWS


RUBY_SIGNALS = set([
    "SIGHUP", "SIGINT", "SIGQUIT", "SIGILL", "SIGTRAP", "SIGIOT", "SIGABRT",
    "SIGEMT", "SIGFPE", "SIGKILL", "SIGBUS", "SIGSEGV", "SIGSYS", "SIGPIPE",
    "SIGALRM", "SIGTERM", "SIGURG", "SIGSTOP", "SIGTSTP", "SIGCONT", "SIGCHLD",
    "SIGCLD", "SIGCHLD", "SIGTTIN", "SIGTTOU", "SIGIO", "SIGXCPU", "SIGXFSZ",
    "SIGVTALRM", "SIGPROF", "SIGWINCH", "SIGUSR1", "SIGUSR2", "SIGLOST",
    "SIGMSG", "SIGPWR", "SIGPOLL", "SIGDANGER", "SIGMIGRATE", "SIGPRE",
    "SIGGRANT", "SIGRETRACT", "SIGSOUND", "SIGINFO",
])

SIGNALS = dict([
    (k[3:], getattr(rsignal, k))
    for k in rsignal.signal_names
    if k in RUBY_SIGNALS
])
SIGNALS["EXIT"] = 0
if not IS_WINDOWS:
    SIGNALS["CLD"] = SIGNALS["CHLD"]


class Signal(object):
    moduledef = ModuleDef("Signal")

    @moduledef.function("trap")
    def method_trap(self, args_w):
        pass

    @moduledef.function("list")
    def method_list(self, space):
        w_res = space.newhash()
        for sig_name, sig_num in SIGNALS.iteritems():
            space.send(w_res, "[]=", [space.newstr_fromstr(sig_name), space.newint(sig_num)])
        return w_res
