from rupypy.error import RubyError
from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_NumericObject(W_Object):
    classdef = ClassDef("Numeric", W_Object.classdef, filepath=__file__)

    @staticmethod
    def retry_binop_coercing(space, w_recv, w_arg, binop, raise_error=True):
        w_ary = None
        try:
            w_ary = space.send(w_recv, space.newsymbol("coerce"), [w_arg])
        except RubyError as e:
            if not space.is_kind_of(e.w_value, space.w_StandardError):
                raise
            if raise_error:
                raise space.error(space.w_ArgumentError,
                    "comparison of %s with %s failed" % (
                        space.getclass(w_recv).name, space.getclass(w_arg).name
                    )
                )
        if space.getclass(w_ary) is space.w_array:
            ary = space.listview(w_ary)
            if len(ary) == 2:
                return space.send(ary[1], space.newsymbol(binop), ary[:1])
        elif raise_error:
            raise space.error(space.w_TypeError, "coerce must return [x, y]")
        else:
            return None

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_NumericObject(space, self)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if self == w_other:
            return space.newint(0)
        else:
            return space.w_nil

    @classdef.method("<=")
    def method_lte(self, space, w_other):
        w_result = space.send(self, space.newsymbol("<=>"), [w_other])
        return space.newbool(not (w_result is space.w_nil or space.int_w(w_result) > 0))

    @classdef.method("coerce")
    def method_coerce(self, space, w_other):
        if space.getclass(w_other) is space.getclass(self):
            return space.newarray([w_other, self])
        else:
            return space.newarray([space.send(self, space.newsymbol("Float"), [w_other]), self])

    classdef.app_method("""
    def eql? other
        self.class.equal?(other.class) && self == other
    end

    def to_int
        self.to_i
    end
    """)
