from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi.type import (W_TypeObject, type_object,
                                    typechars, native_types, ffi_types)
from topaz.modules.ffi.dynamic_library import (W_DL_SymbolObject,
                                               coerce_dl_symbol)
from topaz.modules.ffi.pointer import W_PointerObject, coerce_pointer
from topaz.error import RubyError
from topaz.coerce import Coerce
from topaz.objects.functionobject import W_BuiltinFunction

from rpython.rtyper.lltypesystem import rffi, lltype, llmemory
from rpython.rlib import clibffi
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rarithmetic import intmask, longlongmask
from rpython.rlib.rbigint import rbigint

INT8 = typechars['INT8']
UINT8 = typechars['UINT8']
INT16 = typechars['INT16']
UINT16 = typechars['UINT16']
INT32 = typechars['INT32']
UINT32 = typechars['UINT32']
INT64 = typechars['INT64']
UINT64 = typechars['UINT64']
LONG = typechars['LONG']
ULONG = typechars['ULONG']
FLOAT32 = typechars['FLOAT32']
FLOAT64 = typechars['FLOAT64']
BOOL = typechars['BOOL']
STRING = typechars['STRING']
POINTER = typechars['POINTER']
VOID = typechars['VOID']

unrolling_typechars = unrolling_iterable(typechars.values())

char_native_type_pair = [(typechars[n], native_types[n]) for n in typechars]
unrolling_char_native_type_pair = unrolling_iterable(char_native_type_pair)

class W_FunctionObject(W_PointerObject):
    classdef = ClassDef('Function', W_PointerObject.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FunctionObject(space)

    def __init__(self, space):
        W_PointerObject.__init__(self, space)
        self.w_ret_type = W_TypeObject(space, 'DUMMY')
        self.arg_types_w = []
        self.funcptr = None
        self.ptr = lltype.nullptr(rffi.VOIDP.TO)

    @classdef.method('initialize')
    def method_initialize(self, space, w_ret_type, w_arg_types,
                          w_name=None, w_options=None):
        if w_options is None: w_options = space.newhash()
        self.w_ret_type = type_object(space, w_ret_type)
        self.arg_types_w = [type_object(space, w_type)
                            for w_type in space.listview(w_arg_types)]
        self.ptr = (coerce_dl_symbol(space, w_name) if w_name
                    else lltype.nullptr(rffi.VOIDP.TO))
        ffi_arg_types = [ffi_types[t.typename] for t in self.arg_types_w]
        ffi_ret_type = ffi_types[self.w_ret_type.typename]
        self.funcptr = clibffi.FuncPtr('unattached',
                                       ffi_arg_types, ffi_ret_type,
                                       self.ptr)

    @classdef.method('call')
    def method_call(self, space, args_w):
        w_ret_type = self.w_ret_type
        assert isinstance(w_ret_type, W_TypeObject)
        arg_types_w = self.arg_types_w
        ret_type_name = w_ret_type.typename

        for i in range(len(args_w)):
            for t in unrolling_typechars:
                argtype_name = arg_types_w[i].typename
                if t == typechars[argtype_name]:
                    w_next_arg = self._convert_to_NULL_if_nil(space, args_w[i])
                    self._push_arg(space, w_next_arg, t)
        if typechars[ret_type_name] == VOID:
            self.funcptr.call(lltype.Void)
            return space.w_nil
        for t, nt in unrolling_char_native_type_pair:
            if t == typechars[ret_type_name]:
                result = self.funcptr.call(nt)
                if t == STRING:
                    return self._ruby_wrap_STRING(space, result)
                if t == POINTER:
                    return self._ruby_wrap_POINTER(space, result)
                else:
                    return self._ruby_wrap_number(space, result, t)
        raise Exception("Bug in FFI: unknown Type %s" % ret_type_name)

    def _convert_to_NULL_if_nil(self, space, w_arg):
        if w_arg is space.w_nil:
            w_FFI = space.find_const(space.w_kernel, 'FFI')
            w_Pointer = space.find_const(w_FFI, 'Pointer')
            return space.find_const(w_Pointer, 'NULL')
        else:
            return w_arg

    @specialize.arg(3)
    def _push_arg(self, space, w_arg, typechar):
        for t, nt in unrolling_char_native_type_pair:
            if typechar == t:
                if t == STRING:
                    string_arg = space.str_w(w_arg)
                    charp_arg = rffi.str2charp(string_arg)
                    # XXX: The cast is a workaround because clibffi's
                    # FuncPtr.push_arg (used at the bottom of this function)
                    # has a bug.
                    arg_ll = rffi.cast(rffi.VOIDP, charp_arg)
                elif t == POINTER:
                    arg_ll = coerce_pointer(space, w_arg)
                else:
                    if(t == UINT8 or
                       t == INT8 or
                       t == UINT16 or
                       t == INT16 or
                       t == UINT32 or
                       t == INT32):
                        py_arg = space.int_w(w_arg)
                    elif t == INT64 or t == UINT64:
                        py_arg = space.bigint_w(w_arg).tolonglong()
                    elif t == FLOAT32 or t == FLOAT64:
                        py_arg = space.float_w(w_arg)
                    elif t == LONG or t == ULONG:
                        if rffi.sizeof(nt) < 8:
                            py_arg = intmask(space.int_w(w_arg))
                        else:
                            py_arg = space.bigint_w(w_arg).tolonglong()
                    elif t == BOOL:
                        py_arg = space.is_true(w_arg)
                    else:
                        assert False
                    arg_ll = rffi.cast(nt, py_arg)
                self.funcptr.push_arg(arg_ll)

    @specialize.arg(3)
    def _ruby_wrap_number(self, space, res, restype):
        if restype == INT8:
            int_res = ord(res)
            if int_res >= 128:
                int_res -= 256
            return space.newint(int_res)
        elif (restype == UINT8 or
              restype == UINT16 or
              restype == UINT16 or
              restype == INT16 or
              restype == UINT32 or
              restype == INT32):
            return space.newint(intmask(res))
        elif restype == INT64 or restype == UINT64:
            bigint_res = rbigint.fromrarith_int(longlongmask(res))
            return space.newbigint_fromrbigint(bigint_res)
        elif restype == LONG or restype == ULONG:
            if rffi.sizeof(rffi.LONG) < 8:
                return space.newint(intmask(res))
            else:
                bigint_res = rbigint.fromrarith_int(longlongmask(res))
                return space.newbigint_fromrbigint(bigint_res)
        elif restype == FLOAT32 or restype == FLOAT64:
            return space.newfloat(float(res))
        elif restype == BOOL:
            return space.newbool(res)
        raise Exception("Bug in FFI: unknown Type %s" % restype)

    def _ruby_wrap_STRING(self, space, res):
        str_res = rffi.charp2str(res)
        return space.newstr_fromstr(str_res)

    def _ruby_wrap_POINTER(self, space, res):
        adr_res = llmemory.cast_ptr_to_adr(res)
        int_res = llmemory.cast_adr_to_int(adr_res)
        w_FFI = space.find_const(space.w_kernel, 'FFI')
        w_Pointer = space.find_const(w_FFI, 'Pointer')
        return space.send(w_Pointer, 'new',
                          [space.newint(int_res)])

    @classdef.method('attach', name='str')
    def method_attach(self, space, w_lib, name):
        self.funcptr.name = name
        w_attachments = space.send(w_lib, 'attachments')
        space.send(w_attachments, '[]=', [space.newsymbol(name), self])
