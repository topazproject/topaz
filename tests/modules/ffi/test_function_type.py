from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi import type as ffitype

from rpython.rtyper.lltypesystem import rffi, lltype

class TestFunctionType(BaseFFITest):
    def test_it_has_Type_as_a_superclass(self, space):
        self.ask(space, "FFI::FunctionType.superclass.equal? FFI::Type")

    def test_it_is_also_known_as_FunctionInfo(self, space):
        self.ask(space, "FFI::FunctionType.equal? FFI::FunctionInfo")

    def test_it_is_also_known_as_CallbackInfo(self, space):
        self.ask(space, "FFI::FunctionType.equal? FFI::CallbackInfo")

class TestFunctionType__new(BaseFFITest):
    def test_it_saves_the_args_and_the_ret_types(self, space):
        w_function_type = space.execute("""
        FFI::FunctionType.new(FFI::Type::INT8,
                              [FFI::Type::FLOAT32, FFI::Type::UINT16])
        """)
        assert w_function_type.w_ret_type.typeindex == ffitype.INT8
        arg_indices = [w_t.typeindex for w_t in w_function_type.arg_types_w]
        assert arg_indices == [ffitype.FLOAT32, ffitype.UINT16]

    def test_it_does_not_accept_Symbols(self, space):
        with self.raises(space, 'TypeError', "Invalid parameter type (:int8)"):
            space.execute("FFI::FunctionType.new(:int8, [])")
        with self.raises(space, 'TypeError',
                         "Invalid parameter type (:float64)"):
            space.execute("FFI::FunctionType.new(FFI::Type::INT8, [:float64])")

    def test_it_has_a_Hash_as_optional_3rd_argument(self, space):
        w_function_type = space.execute("""
        FFI::FunctionType.new(FFI::Type::VOID, [], {convention: :default})
        """)
        w_res = space.send(w_function_type.w_options, '[]',
                           [space.newsymbol('convention')])
        assert self.unwrap(space, w_res) == 'default'

    def test_it_creates_an_empty_hash_if_no_options_were_given(self, space):
        w_function_type = space.execute("""
        FFI::FunctionType.new(FFI::Type::VOID, [])
        """)
        assert space.is_true(space.send(w_function_type.w_options, 'empty?'))

    # If you don't use a Hash as a third argument anything might happen (e.g.
    # segfault). This is also the behaviour of the original ruby ffi.

class TestFunctionType_py_invoke(BaseFFITest):
    def test_it_invokes_the_given_proc_with_ll_args(self, space):
        w_func_type = space.execute("""
        int32 = FFI::Type::INT32
        func_type = FFI::FunctionType.new(int32,
                    [int32, int32])
        """)
        w_proc = space.execute("proc { |x, y| x + y }")
        p_arg1 = lltype.malloc(rffi.CCHARP.TO, 1, flavor='raw')
        p_arg2 = lltype.malloc(rffi.CCHARP.TO, 1, flavor='raw')
        p_args = lltype.malloc(rffi.CCHARPP.TO, 2, flavor='raw')
        p_res = lltype.malloc(rffi.INTP.TO, 1, flavor='raw')
        try:
            p_arg1[0] = rffi.cast(rffi.CHAR, 1)
            p_arg2[0] = rffi.cast(rffi.CHAR, 2)
            p_args[0] = p_arg1
            p_args[1] = p_arg2
            w_func_type.invoke(w_proc, p_res, p_args)
            assert p_res[0] == 3
        finally:
            lltype.free(p_arg1, flavor='raw')
            lltype.free(p_arg2, flavor='raw')
            lltype.free(p_args, flavor='raw')
            lltype.free(p_res, flavor='raw')
