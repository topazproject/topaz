from tests.modules.ffi.base import BaseFFITest
from topaz.objects.classobject import W_ClassObject
from topaz.modules.ffi.function import W_FunctionObject
from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

libm = clibffi.CDLL('libm.so')

class TestFunction(BaseFFITest):

    def test_ensure_w_type(self, space):
        w_type_object = space.execute("FFI::Type::VOID")
        w_type_symbol = space.execute(":void")
        w_some_int = space.execute("1")
        w_unknown_type = space.execute(":int42")
        assert (W_FunctionObject.ensure_w_type(space, w_type_object)
                is w_type_object)
        assert (W_FunctionObject.ensure_w_type(space, w_type_symbol)
                is w_type_object)
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            W_FunctionObject.ensure_w_type(space, w_some_int)
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            W_FunctionObject.ensure_w_type(space, w_unknown_type)

    def test_it_has_FFI_Pointer_as_ancestor(self, space):
        assert self.ask(space, "FFI::Function.ancestors.include? FFI::Pointer")


class TestFunction__new(BaseFFITest):
    def test_it_needs_at_least_a_type_signature(self, space):
        space.execute("FFI::Function.new(:void, [:int8, :int16])")

    def test_it_takes_a_DynamicLibrabry__Symbol_as_3_argument(self, space):
        space.execute("""
        dlsym = FFI::DynamicLibrary::Symbol.new(:fname)
        FFI::Function.new(:void, [:int8, :int16], dlsym)
        """)
        with self.raises(space, "TypeError",
                      "can't convert Fixnum into FFI::DynamicLibrary::Symbol"):
            space.execute("FFI::Function.new(:void, [:uint8], 500)")

    def test_it_takes_a_hash_as_4_argument(self, space):
        space.execute("""
        FFI::Function.new(:void, [:int8, :int16],
                          FFI::DynamicLibrary::Symbol.new('x'),
                          {})
        """)

    def test_it_understands_Type_constants_for_the_signature(self, space):
        space.execute("""
        FFI::Function.new(FFI::Type::VOID,
                          [FFI::Type::INT8, FFI::Type::INT16])
        """)

    def test_it_reacts_to_messy_signature_with_TypeError(self, space):
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(1, [])")
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(:void, [2])")
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:null, [])")
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:int32, [:array])")

    def test_it_creates_the_following_low_level_data(self, space):
        w_function = space.execute("""
        foo = FFI::DynamicLibrary::Symbol.new(:foo)
        FFI::Function.new(:int8, [:int16, :float64], foo, {})
        """)
        w_short = space.execute("FFI::Type::SHORT")
        w_double = space.execute("FFI::Type::DOUBLE")
        w_char = space.execute("FFI::Type::CHAR")
        assert w_function.arg_types_w == [w_short, w_double]
        assert w_function.w_ret_type == w_char
        assert w_function.name == 'foo'

class TestFunction_attach(BaseFFITest):
    def test_it_works_with_pow_from_libm(self, space):
        w_res = space.execute("""
        class LibraryMock
            def initialize
                local = FFI::DynamicLibrary::RTLD_LOCAL
                @ffi_libs = [FFI::DynamicLibrary.open('libm.so', local)]
            end
            attr_reader :attachments
        end
        lib = LibraryMock.new
        oo_pow = FFI::DynamicLibrary::Symbol.new(:pow)
        func = FFI::Function.new(:float64, [:float64, :float64], oo_pow, {})
        func.attach(lib, 'power')
        lib.attachments.include? :power
        (0..5).each.map { |x| lib.attachments[:power].call(x, 2) }
        """)
        res = self.unwrap(space, w_res)
        assert [x for x in res] == [0.0, 1.0, 4.0, 9.0, 16.0, 25.0]

    def test_it_works_with_abs_from_libc(self, space):
        w_res = space.execute("""
        class LibraryMock
            def initialize
                local = FFI::DynamicLibrary::RTLD_LOCAL
                @ffi_libs = [FFI::DynamicLibrary.open('libc.so.6', local)]
            end
            attr_reader :attachments
        end
        lib = LibraryMock.new
        oo_abs = FFI::DynamicLibrary::Symbol.new(:abs)
        FFI::Function.new(:int32, [:int32], oo_abs, {}).attach(lib, 'abs')
        lib.attachments.include? :abs
        (-3..+3).each.map { |x| lib.attachments[:abs].call(x) }
        """)
        assert self.unwrap(space, w_res) == [3, 2, 1, 0, 1, 2, 3]
