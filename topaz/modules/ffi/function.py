from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi.type import (W_TypeObject, type_object,
                                    native_types, ffi_types)
from topaz.modules.ffi.dynamic_library import W_DL_SymbolObject
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.error import RubyError
from topaz.coerce import Coerce
from topaz.objects.functionobject import W_BuiltinFunction

from rpython.rtyper.lltypesystem import rffi, lltype, llmemory
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
        self.w_name = space.newsymbol('')

    @classdef.method('initialize')
    def method_initialize(self, space, w_ret_type, w_arg_types,
                          w_name=None, w_options=None):
        if w_options is None: w_options = space.newhash()
        self.w_ret_type = type_object(space, w_ret_type)
        self.arg_types_w = [type_object(space, w_type)
                            for w_type in space.listview(w_arg_types)]
        self.w_name = self.dlsym_unwrap(space, w_name) if w_name else None

    @staticmethod
    def dlsym_unwrap(space, w_name):
        try:
            return space.send(w_name, 'to_sym')
        except RubyError:
            raise space.error(space.w_TypeError,
                            "can't convert %s into FFI::DynamicLibrary::Symbol"
                              % w_name.getclass(space).name)

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
                    arg = self._get_arg(space, args_w[i], t)
                    self.funcptr.push_arg(arg)
        for t in unrolling_rettypes:
            if t == ret_type_name:
                if self.ptr != lltype.nullptr(rffi.VOIDP.TO):
                    if t == 'VOID':
                        self._call_ptr_without_result()
                        return space.w_nil
                    else:
                        result = self._call_ptr(t)
                        return self._ruby_wrap(space, result, t)
                else:
                    raise Exception("%s was called before being attached."
                                    % self)

    @specialize.arg(3)
    def _get_arg(self, space, arg, argtype):
        if argtype == 'STRING':
            arg_as_string = space.str_w(arg)
            argval = rffi.str2charp(arg_as_string)
        elif argtype == 'POINTER':
            argval = arg.ptr
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
        return argval

    @specialize.arg(1)
    def _call_ptr(self, restype):
        result = self.funcptr.call(native_types[restype])
        # Is this really necessary (untranslated, it's not)?
        # Maybe call does this anyway:
        casted_result = rffi.cast(native_types[restype], result)
        return casted_result

    def _call_ptr_without_result(self):
        self.funcptr.call(lltype.Void)

    @specialize.arg(3)
    def _ruby_wrap(self, space, res, restype):
        if restype in ['INT8', 'UINT8',
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
        elif restype == 'STRING':
            return space.newstr_fromstr(rffi.charp2str(res))
        elif restype == 'POINTER':
            adr_res = llmemory.cast_ptr_to_adr(res)
            int_res = llmemory.cast_adr_to_int(adr_res)
            w_FFI = space.find_const(space.w_kernel, 'FFI')
            w_Pointer = space.find_const(w_FFI, 'Pointer')
            return space.send(w_Pointer, 'new', [space.newint(int_res)])
        raise Exception("Bug in FFI: unknown Type %s" % t)

    @classdef.method('attach', name='str')
    def method_attach(self, space, w_lib, name):
        w_ret_type = self.w_ret_type
        arg_types_w = self.arg_types_w
        w_ffi_libs = space.find_instance_var(w_lib, '@ffi_libs')
        for w_dl in w_ffi_libs.listview(space):
            ffi_arg_types = [ffi_types[t.name] for t in arg_types_w]
            ffi_ret_type = ffi_types[w_ret_type.name]
            ptr_key = self.w_name
            assert space.is_kind_of(ptr_key, space.w_symbol)
            try:
                self.funcptr = w_dl.getpointer(space.symbol_w(ptr_key),
                                               ffi_arg_types,
                                               ffi_ret_type)
                self.ptr = self.funcptr.funcsym
                w_attachments = space.send(w_lib, 'attachments')
                space.send(w_attachments, '[]=', [space.newsymbol(name), self])
            except KeyError: pass
