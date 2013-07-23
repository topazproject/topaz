from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi.type import (W_TypeObject, type_object,
                                    native_types, ffi_types)
from topaz.modules.ffi.dynamic_library import W_DL_SymbolObject
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.error import RubyError
from topaz.coerce import Coerce
from topaz.objects.functionobject import W_BuiltinFunction

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib import clibffi
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rbigint import rbigint

unrolling_types = unrolling_iterable([
                                      'INT32',
                                      'FLOAT64',
                                      'STRING'
                                    ])

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
        self.ptr = None

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
            for t in unrolling_types:
                argtype_name = arg_types_w[i].name
                if t == argtype_name:
                    self._push_arg(space, args_w[i], t)
        for t in unrolling_types:
            if t == ret_type_name:
                result = self.ptr.call(native_types[t])
                # Is this really necessary? Maybe call does this anyway:
                result = rffi.cast(native_types[t], result)
                if t == 'INT32':
                    bigres = rbigint.fromrarith_int(result)
                    return space.newbigint_fromrbigint(bigres)
                elif t == 'FLOAT64':
                    return space.newfloat(result)
                elif t == 'STRING':
                    return space.newstr_fromstr(rffi.charp2str(result))
        assert False
        return space.w_nil

    @specialize.arg(3)
    def _push_arg(self, space, arg, argtype):
        if argtype == 'INT32':
            argval = space.int_w(arg)
        elif argtype == 'FLOAT64':
            argval = space.float_w(arg)
        elif argtype == 'STRING':
            string = space.str_w(arg)
            argval = lltype.malloc(rffi.CArray(rffi.CHAR), len(string),
                                 flavor='raw')
            for i in range(len(string)):
                argval[i] = string[i]
        else:
            assert False
        self.ptr.push_arg(argval)

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
                self.ptr = w_dl.getpointer(space.symbol_w(ptr_key),
                                           ffi_arg_types,
                                           ffi_ret_type)
                w_attachments = space.send(w_lib, 'attachments')
                space.send(w_attachments, '[]=', [space.newsymbol(name), self])
            except KeyError: pass
