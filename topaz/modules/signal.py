from __future__ import absolute_import

from rpython.rlib import rsignal

from topaz.module import ModuleDef


SIGNALS = dict([
    (k[3:], getattr(rsignal, k))
    for k in rsignal.signal_names
])
SIGNALS["EXIT"] = 0
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
