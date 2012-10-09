from rupypy.error import RubyError
from rupypy.module import ClassDef
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.objectobject import W_Object


class W_NumericObject(W_Object):
    classdef = ClassDef("Numeric", W_Object.classdef)

    @staticmethod
    def retry_binop_coercing(space, w_recv, w_arg, binop):
        try:
            w_ary = space.send(w_recv, space.newsymbol("coerce"), [w_arg])
            if isinstance(w_ary, W_ArrayObject):
                ary = space.listview(w_ary)
                if len(ary) == 2:
                    return space.send(ary[1], space.newsymbol(binop), ary[:1])
        except RubyError:
            raise space.error(
                space.w_ArgumentError,
                "comparison of %s with %s failed" % (
                    space.getclass(w_recv).name, space.getclass(w_arg).name
                )
            )

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if self == w_other:
            return space.newint(0)
        else:
            return space.w_nil

    @classdef.method("<=")
    def method_let(self, space, w_other):
        cmpresult = space.send(self, space.newsymbol("<=>"), [w_other])
        if cmpresult is space.w_nil or space.int_w(cmpresult) > 0:
            return space.w_false
        else:
            return space.w_true

    @classdef.method("coerce")
    def method_coerce(self, space, w_other):
        if space.getclass(w_other) == space.getclass(self):
            return space.newarray([w_other, self])
        else:
            return space.newarray([space.send(self, space.newsymbol("Float"), [w_other]), self])

    @classdef.method("to_int")
    def method_to_int(self, space):
        return space.send(self, space.newsymbol("to_i"))

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_NumericObject(space, self)
