from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef

class W_PointerObject(W_Object):
    classdef = ClassDef('Pointer', W_Object.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_PointerObject(space)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(w_cls, 'NULL', W_PointerObject(space))

    @classdef.singleton_method('new', arg='int')
    def singleton_method_new(self, space, arg):
        if arg == 0:
            return space.find_const(self, 'NULL')
        else:
            return W_PointerObject(space)

    @classdef.method('null?')
    def method_null_p(self, space):
        w_null_instance = space.find_const(self.getclass(space), 'NULL')
        return space.newbool(self is w_null_instance)

    @classdef.method('address')
    def method_address(self, space):
        return space.newint(0)

    @classdef.method('+')
    def method_plus(self, space, w_other):
        return space.newint(0)

    # TODO: actually all Numerics should be accepted
    @classdef.method('slice', offset='int', length='int')
    def method_address(self, space, offset, length):
        return space.newint(0)

    @classdef.method('to_i')
    def method_to_i(self, space):
        return space.newint(0)

    @classdef.method('order', endianness='symbol')
    def method_order(self, space, endianness):
        return space.newint(0)

    @classdef.method('autorelease=', val='bool')
    def method_autorelease_eq(self, space, val):
        self.autorelease = val
        return space.newbool(val)

    @classdef.method('autorelease?')
    def method_autorelease_p(self, space):
        return space.newbool(self.autorelease)

    @classdef.method('free')
    def method_free(self, space):
        # TODO: Free stuff self is pointing at here
        return self

    @classdef.method('type_size')
    def method_type_size(self, space):
        return space.newint(0)
