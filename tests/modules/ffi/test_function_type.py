from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi import type as ffitype

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
