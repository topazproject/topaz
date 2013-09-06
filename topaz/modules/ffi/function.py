from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi.type import (W_TypeObject, type_object,
                                    native_types, ffi_types)
from topaz.modules.ffi.dynamic_library import (W_DL_SymbolObject,
                                               coerce_dl_symbol)
from topaz.modules.ffi.pointer import W_PointerObject, coerce_pointer
from topaz.error import RubyError
from topaz.coerce import Coerce
from topaz.objects.functionobject import W_BuiltinFunction

from rpython.rtyper.lltypesystem import rffi, lltype, llmemory
from rpython.rtyper.lltypesystem.llmemory import (cast_int_to_adr as int2adr,
                                                  cast_adr_to_ptr as adr2ptr)
from rpython.rlib import clibffi
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rarithmetic import intmask, longlongmask
from rpython.rlib.rbigint import rbigint

valid_argtypes = [
                  'UINT8',
                  'INT8',
                  'UINT16',
                  'INT16',
                  'INT32',
                  'UINT32',
                  'INT64',
                  'UINT64',
                  'FLOAT64',
                  'BOOL',
                  'STRING',
                  'POINTER'
                 ]

unrolling_argtypes = unrolling_iterable(valid_argtypes)
unrolling_rettypes = unrolling_iterable(valid_argtypes + ['VOID'])

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
        self.ptr = rffi.NULL

    @classdef.method('initialize')
    def method_initialize(self, space, w_ret_type, w_arg_types,
                          w_name=None, w_options=None):
        if w_options is None: w_options = space.newhash()
        self.w_ret_type = type_object(space, w_ret_type)
        self.arg_types_w = [type_object(space, w_type)
                            for w_type in space.listview(w_arg_types)]
        self.ptr = coerce_dl_symbol(space, w_name) if w_name else None
        ffi_arg_types = [ffi_types[t.name] for t in self.arg_types_w]
        ffi_ret_type = ffi_types[self.w_ret_type.name]
        self.funcptr = clibffi.FuncPtr('unattached',
                                       ffi_arg_types, ffi_ret_type,
                                       self.ptr)

    @classdef.method('call')
    def method_call(self, space, args_w):
        w_ret_type = self.w_ret_type
        assert isinstance(w_ret_type, W_TypeObject)
        arg_types_w = self.arg_types_w
        ret_type_name = w_ret_type.name

        for i in range(len(args_w)):
            for t in unrolling_argtypes:
                argtype_name = arg_types_w[i].name
                if t == argtype_name:
                    self._push_arg(space, args_w[i], t)
        if ret_type_name == 'VOID':
            self.funcptr.call(lltype.Void)
            return space.w_nil
        for t in unrolling_argtypes:
            if t == ret_type_name:
                result = self.funcptr.call(native_types[t])
                if t == 'STRING':
                    return self._ruby_wrap_STRING(space, result)
                if t == 'POINTER':
                    return self._ruby_wrap_POINTER(space, result)
                else:
                    return self._ruby_wrap_number(space, result, t)
        raise Exception("Bug in FFI: unknown Type %s" % ret_type_name)

    @specialize.arg(3)
    def _push_arg(self, space, arg, argtype):
        if argtype == 'STRING':
            string_arg = space.str_w(arg)
            charp_arg = rffi.str2charp(string_arg)
            argval = rffi.cast(rffi.VOIDP, charp_arg)
        elif argtype == 'POINTER':
                argval = coerce_pointer(space, arg)
        else:
            if argtype in ['UINT8', 'INT8',
                           'UINT16', 'INT16',
                           'UINT32', 'INT32']:
                argval = space.int_w(arg)
            elif argtype in ['INT64', 'UINT64']:
                argval = space.bigint_w(arg).tolonglong()
            elif argtype == 'FLOAT64':
                argval = space.float_w(arg)
            elif argtype == 'BOOL':
                argval = space.is_true(arg)
            else:
                assert False
        self.funcptr.push_arg(argval)

    @specialize.arg(3)
    def _ruby_wrap_number(self, space, res, restype):
        if restype == 'INT8':
            int_res = ord(res)
            if int_res >= 128:
                int_res -= 256
            return space.newint(int_res)
        elif restype in ['UINT8',
                         'UINT16', 'INT16',
                         'UINT32', 'INT32']:
            return space.newint(intmask(res))
        elif restype in ['INT64', 'UINT64']:
            longlong_res = longlongmask(res)
            bigint_res = rbigint.fromrarith_int(longlong_res)
            return space.newbigint_fromrbigint(bigint_res)
        elif restype == 'FLOAT64':
            return space.newfloat(res)
        elif restype == 'BOOL':
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
