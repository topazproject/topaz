from topaz.modules.ffi.abstract_memory import W_AbstractMemoryObject
from topaz.module import ClassDef
from topaz.coerce import Coerce

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype

def coerce_pointer(space, w_pointer):
    if isinstance(w_pointer, W_PointerObject):
        return w_pointer.ptr
    else:
        raise space.error(space.w_TypeError,
                          "%s is not a pointer." % w_pointer)

setattr(Coerce, 'ffi_pointer', staticmethod(coerce_pointer))

def coerce_address(space, w_addressable):
    if space.is_kind_of(w_addressable, space.w_fixnum):
        w_address = w_addressable
    elif space.is_kind_of(w_addressable,
                          space.getclassfor(W_PointerObject)):
        w_address = space.send(w_addressable, 'address')
    else:
        assert False #TODO: raise better exception
    return Coerce.int(space, w_address)

setattr(Coerce, 'ffi_address', staticmethod(coerce_address))

class W_PointerObject(W_AbstractMemoryObject):
    classdef = ClassDef('Pointer', W_AbstractMemoryObject.classdef)

    def __init__(self, space):
        W_AbstractMemoryObject.__init__(self, space)
        self.address = -1
        self.ptr = lltype.nullptr(rffi.VOIDP.TO)
        self.sizeof_type = -1
        self.sizeof_memory = -1

    def __deepcopy__(self, memo):
        obj = super(W_AbstractMemoryObject, self).__deepcopy__(memo)
        obj.address = self.address
        obj.sizeof_memory = self.sizeof_memory
        return obj

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space):
        return W_PointerObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, args_w):
        if len(args_w) == 1:
            address = coerce_address(space, args_w[0])
            return self._initialize(space, address)
        elif len(args_w) == 2:
            sizeof_type = Coerce.int(space, args_w[0])
            address = coerce_address(space, args_w[1])
            return self._initialize(space, address, sizeof_type)

    def _initialize(self, space, address, sizeof_type=1):
        W_AbstractMemoryObject.__init__(self, space)
        self.address = address
        self.ptr = rffi.cast(rffi.VOIDP, address)
        self.sizeof_type = sizeof_type
        self.sizeof_memory = 2**63

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        w_null = space.send(w_cls, 'new', [space.newint(0)])
        space.set_const(w_cls, 'NULL', w_null)
        space.send(w_cls, 'alias_method', [space.newsymbol('to_i'),
                                           space.newsymbol('address')])
        space.send(w_cls, 'alias_method', [space.newsymbol('[]'),
                                           space.newsymbol('+')])

    @classdef.method('free')
    def method_free(self, space):
        lltype.free(self.ptr, flavor='raw')

    @classdef.method('null?')
    def method_null_p(self, space):
        return space.newbool(self.address == 0)

    @classdef.method('address')
    def method_address(self, space):
        return space.newint(self.address)

    @classdef.method('size')
    def method_size(self, space):
        return space.newint_or_bigint(self.sizeof_memory)

    @classdef.method('==')
    def method_eq(self, space, w_other):
        if isinstance(w_other, W_PointerObject):
            return space.newbool(self.address == w_other.address)
        else:
            return space.newbool(False)

    @classdef.method('+', other='int')
    def method_plus(self, space, other):
        w_ptr_sum = space.newint(self.address + other)
        return space.send(space.getclass(self), 'new', [w_ptr_sum])

    @classdef.method('slice', size='int')
    def method_address(self, space, w_offset, size):
        w_pointer = space.send(self, '+', [w_offset])
        assert isinstance(w_pointer, W_PointerObject)
        w_pointer.sizeof_memory = size
        return w_pointer

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
        return space.newint(self.sizeof_type)
