from tests.base import BaseTopazTest
from topaz.objects.classobject import W_ClassObject
from topaz.modules.ffi.function import W_FunctionObject
from rpython.rlib import clibffi

libm = clibffi.CDLL('libm.so')

class TestFunction(BaseTopazTest):

    def test_type_unwrap(self, space):
        w_type_object = space.execute("FFI::Type::VOID")
        w_type_symbol = space.execute(":void")
        w_some_int = space.execute("1")
        w_unknown_type = space.execute(":int42")
        assert (W_FunctionObject.type_unwrap(space, w_type_object)
                is w_type_object.ffi_type)
        assert (W_FunctionObject.type_unwrap(space, w_type_symbol)
                is w_type_object.ffi_type)
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            W_FunctionObject.type_unwrap(space, w_some_int)
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            W_FunctionObject.type_unwrap(space, w_unknown_type)

    def test_initialize_typing(self, space):
        fname = "FFI::DynamicLibrary::Symbol.new(:fname)"
        w_function = space.execute("""
        FFI::Function.new(:void, [:int8, :int16], %s, {})
        """ % fname) #didn't crash
        w_function = space.execute("""
        FFI::Function.new(FFI::Type::VOID,
                          [FFI::Type::INT8, FFI::Type::INT16], %s, {})
        """ % fname) # didn't crash
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(1, [], %s, {})" % fname)
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(:void, [2], %s, {})" % fname)
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:null, [], %s, {})" % fname)
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:int32, [:array], %s, {})"
                          % fname)
        with self.raises(space, "TypeError",
                         "can't convert Fixnum into Symbol"):
            space.execute("FFI::Function.new(:void, [:uint8], 500, {})")

    def test_initialize_setvars(self, space):
        w_function = space.execute("""
        foo = FFI::DynamicLibrary::Symbol.new(:foo)
        FFI::Function.new(:int8, [:int16, :float64], foo, {})
        """)
        assert w_function.arg_types == [clibffi.ffi_type_sint16,
                                        clibffi.ffi_type_double]
        assert w_function.ret_type == clibffi.ffi_type_sint8
        assert w_function.name == 'foo'

    def test_attach(self, space):
        w_res = space.execute("""
        class LibraryMock
            def initialize
                local = FFI::DynamicLibrary::RTLD_LOCAL
                @ffi_libs = [FFI::DynamicLibrary.open('libm.so', local)]
            end
        end
        lib = LibraryMock.new
        pow = FFI::DynamicLibrary::Symbol.new(:pow)
        func = FFI::Function.new(:float64, [:float64, :float64], pow, {})
        func.attach(lib, 'power')
        floor = FFI::DynamicLibrary::Symbol.new(:floor)
        FFI::Function.new(:float64, [:float64], floor, {}).attach(lib, 'floor')
        arr1 = (0..5).each.map { |x| lib.power(x, 2) }
        arr2 = [1.1, 1.3, 1.6, 1.9].each.map { |x| lib.floor(x) }
        arr1 + arr2
        """)
        res = self.unwrap(space, w_res)
        for i in range(6):
            assert res[i] == i*i
        assert all([x == 1 for x in res[6:]])
