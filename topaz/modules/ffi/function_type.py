from topaz.modules.ffi.type import W_TypeObject
from topaz.modules.ffi import type as ffitype
from topaz.module import ClassDef

from rpython.rlib.objectmodel import specialize
from rpython.rlib.rarithmetic import intmask, longlongmask

for i, name in enumerate(ffitype.type_names):
    globals()[name] = i

def raise_TypeError_if_not_TypeObject(space, w_candidate):
    if not space.is_kind_of(w_candidate, space.getclassfor(W_TypeObject)):
        raise space.error(space.w_TypeError,
                          "Invalid parameter type (%s)" %
                          space.str_w(space.send(w_candidate, 'inspect')))

class W_FunctionTypeObject(W_TypeObject):
    classdef = ClassDef('FunctionType', W_TypeObject.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FunctionTypeObject(space)

    @classdef.method('initialize', arg_types_w='array')
    def method_initialize(self, space, w_ret_type, arg_types_w, w_options=None):
        if w_options is None:
            w_options = space.newhash()
        self.w_options = w_options

        raise_TypeError_if_not_TypeObject(space, w_ret_type)
        for w_arg_type in arg_types_w:
            raise_TypeError_if_not_TypeObject(space, w_arg_type)

        self.w_ret_type = w_ret_type
        self.arg_types_w = arg_types_w

    def invoke(self, space, w_proc, *ll_args):
        args_w = []
        for i in range(len(self.arg_types_w)):
            w_arg_type = self.arg_types_w[i]
            ll_arg = ll_args[i]
            t = w_arg_type.typeindex
            if t == STRING:
                w_arg = self._ruby_wrap_STRING(space, ll_arg)
            elif t == POINTER:
                w_arg = self._ruby_wrap_POINTER(space, ll_arg)
            else:
                w_arg = self._ruby_wrap_number(space, ll_arg, t)
            args_w.append(w_arg)
        return space.send(w_proc, 'call', args_w)

    @specialize.arg(3)
    def _ruby_wrap_number(self, space, res, restype):
        if restype == INT8:
            if res >= 128:
                res -= 256
            return space.newint(res)
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
        int_res = rffi.cast(lltype.Signed, res)
        w_FFI = space.find_const(space.w_kernel, 'FFI')
        w_Pointer = space.find_const(w_FFI, 'Pointer')
        return space.send(w_Pointer, 'new',
                          [space.newint(int_res)])
