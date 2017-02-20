import math

from rpython.rlib.rfloat import round_away

from topaz.coerce import Coerce
from topaz.error import RubyError
from topaz.module import ClassDef
from topaz.modules.comparable import Comparable
from topaz.objects.objectobject import W_Object


class W_NumericObject(W_Object):
    classdef = ClassDef("Numeric", W_Object.classdef)
    classdef.include_module(Comparable)

    @staticmethod
    def retry_binop_coercing(space, w_recv, w_arg, binop, raise_error=True):
        w_ary = None
        try:
            w_ary = space.send(w_recv, "coerce", [w_arg])
        except RubyError as e:
            if not space.is_kind_of(e.w_value, space.w_StandardError):
                raise
            space.mark_topframe_not_escaped()
            if raise_error:
                raise space.error(space.w_ArgumentError,
                    "comparison of %s with %s failed" % (
                        space.obj_to_s(space.getclass(w_recv)),
                        space.obj_to_s(space.getclass(w_arg))
                    )
                )
        if space.getclass(w_ary) is space.w_array:
            ary = space.listview(w_ary)
            if len(ary) == 2:
                return space.send(ary[1], binop, ary[:1])
        elif raise_error:
            raise space.error(space.w_TypeError, "coerce must return [x, y]")
        else:
            return None

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_NumericObject(space, self)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if self == w_other:
            return space.newint(0)
        else:
            return space.w_nil

    @classdef.method("<=")
    def method_lte(self, space, w_other):
        w_result = space.send(self, "<=>", [w_other])
        return space.newbool(not (w_result is space.w_nil or space.int_w(w_result) > 0))

    @classdef.method("coerce")
    def method_coerce(self, space, w_other):
        if space.getclass(w_other) is space.getclass(self):
            return space.newarray([w_other, self])
        else:
            return space.newarray([space.send(self, "Float", [w_other]), self])

    @classdef.method("ceil")
    def method_ceil(self, space):
        return space.newint(int(math.ceil(Coerce.float(space, self))))

    @classdef.method("floor")
    def method_floor(self, space):
        return space.newint(int(math.floor(Coerce.float(space, self))))

    @classdef.method("round")
    def method_round(self, space):
        return space.newint(int(round_away(Coerce.float(space, self))))

    @classdef.method("quo")
    def method_quo(self, space):
        raise space.error(space.w_NotImplementedError, "Numeric#quo")
