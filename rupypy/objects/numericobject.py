from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_NumericObject(W_Object):
    classdef = ClassDef("Numeric", W_Object.classdef)

    def float_w(self, space):
        raise NotImplementedError("%s should have implemented float_w" % W_NumericObject.classdef.name)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_NumericObject(space, self)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if self == w_other:
            return space.newint(0)
        else:
            return space.w_nil

    classdef.app_method("""
    def eql? other
        if not self.class.equal?(other.class)
            false
        else
            self == other
        end
    end
    """)

    @classdef.method("to_int")
    def method_to_int(self, space):
        return space.send(self, space.newsymbol("to_i"))
