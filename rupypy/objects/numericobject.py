from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_NumericObject(W_Object):
    classdef = ClassDef("Numeric", W_Object.classdef)

    def float_w(self, space):
        raise NotImplementedError("my subclass should have implemented #float_w")

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
