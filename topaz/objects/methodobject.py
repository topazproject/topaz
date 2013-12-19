from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


def create_owner(classdef):
    @classdef.method("owner")
    def method_owner(self, space):
        return self.w_owner
    return method_owner


def create_to_s(classdef):
    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(
            "#<%s: %s#%s>" % (classdef.name, self.w_owner.name, self.w_function.name)
        )
    return method_to_s


class W_MethodObject(W_Object):
    classdef = ClassDef("Method", W_Object.classdef)

    def __init__(self, space, w_owner, w_function, w_receiver):
        W_Object.__init__(self, space)
        self.w_owner = w_owner
        self.w_function = w_function
        self.w_receiver = w_receiver

    method_allocate = classdef.undefine_allocator()
    method_owner = create_owner(classdef)
    method_to_s = create_to_s(classdef)

    @classdef.method("[]")
    @classdef.method("call")
    def method_call(self, space, args_w, block):
        return space.invoke_function(
            self.w_function,
            self.w_receiver,
            args_w,
            block
        )

    @classdef.method("unbind")
    def method_unbind(self, space):
        return W_UnboundMethodObject(space, self.w_owner, self.w_function)

    @classdef.method("receiver")
    def method_receiver(self, space):
        return self.w_receiver

    @classdef.method("==")
    def method_eql(self, space, w_other):
        if isinstance(w_other, W_MethodObject):
            return space.newbool(
                self.w_function is w_other.w_function and self.w_receiver is w_other.w_receiver
            )
        else:
            return space.w_false

    @classdef.method("arity")
    def method_arity(self, space):
        return self.w_function.arity(space)


class W_UnboundMethodObject(W_Object):
    classdef = ClassDef("UnboundMethod", W_Object.classdef)

    def __init__(self, space, w_owner, w_function):
        W_Object.__init__(self, space)
        self.w_owner = w_owner
        self.w_function = w_function

    method_allocator = classdef.undefine_allocator()
    method_owner = create_owner(classdef)
    method_to_s = create_to_s(classdef)

    @classdef.method("bind")
    def method_bind(self, space, w_receiver):
        if not self.w_owner.is_ancestor_of(space.getclass(w_receiver)):
            raise space.error(space.w_TypeError,
                "bind argument must be an instance of %s" % self.w_owner.name
            )
        else:
            return W_MethodObject(space, self.w_owner, self.w_function, w_receiver)

    @classdef.method("==")
    def method_eql(self, space, w_other):
        if isinstance(w_other, W_UnboundMethodObject):
            return space.newbool(self.w_function is w_other.w_function)
        else:
            return space.w_false

    @classdef.method("arity")
    def method_arity(self, space):
        return self.w_function.arity(space)
