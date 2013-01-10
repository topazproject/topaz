from __future__ import absolute_import

from pypy.rlib import rgc

from topaz.module import Module, ModuleDef
from topaz.objects.objectobject import W_BaseObject


def try_cast_gcref_to_w_baseobject(gcref):
    return rgc.try_cast_gcref_to_instance(W_BaseObject, gcref)


def clear_gcflag_extra(pending):
    while pending:
        gcref = pending.pop()
        if rgc.get_gcflag_extra(gcref):
            rgc.toggle_gcflag_extra(gcref)
            pending.extend(rgc.get_rpy_referents(gcref))


class ObjectSpace(Module):
    moduledef = ModuleDef("ObjectSpace", filepath=__file__)

    @moduledef.function("each_object")
    def method_each_object(self, space, w_mod, block):
        match_w = []
        roots = [gcref for gcref in rgc.get_rpy_roots() if gcref]
        pending = roots[:]
        while pending:
            gcref = pending.pop()
            if not rgc.get_gcflag_extra(gcref):
                rgc.toggle_gcflag_extra(gcref)
                w_obj = try_cast_gcref_to_w_baseobject(gcref)
                if w_obj is not None and space.is_kind_of(w_obj, w_mod):
                    match_w.append(w_obj)
                pending.extend(rgc.get_rpy_referents(gcref))
        clear_gcflag_extra(roots)
        for w_obj in match_w:
            space.invoke_block(block, [w_obj])
