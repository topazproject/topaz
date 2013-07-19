from tests.modules.ffi.base import BaseFFITest
from topaz.objects.classobject import W_ClassObject
from topaz.modules.ffi.function import W_FunctionObject
from topaz.modules.ffi.type import ffi_types, aliases

from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

libm = clibffi.CDLL('libm.so')

class TestFunction(BaseFFITest):

    def test_ensure_w_type(self, space):
        ensure_w_type = W_FunctionObject.ensure_w_type
        for typename in ffi_types:
            w_type_object = space.execute("FFI::Type::%s" % typename)
            assert (ensure_w_type(space, w_type_object)
                    is w_type_object)
            w_type_symbol = space.newsymbol(typename.lower())
            assert (ensure_w_type(space, w_type_symbol)
                    is w_type_object)
            for alias in aliases[typename]:
                assert (ensure_w_type(space, space.newsymbol(alias.lower()))
                        is space.execute("FFI::Type::%s" % typename))

    def test_ensure_w_type_errors(self, space):
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            W_FunctionObject.ensure_w_type(space, space.newint(1))
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            W_FunctionObject.ensure_w_type(space, space.newsymbol('int42'))

    def test_it_has_FFI_Pointer_as_ancestor(self, space):
        assert self.ask(space, "FFI::Function.ancestors.include? FFI::Pointer")

class TestFunction__new(BaseFFITest):

    def test_it_needs_at_least_a_type_signature(self, ffi_space):
        ffi_space.execute("FFI::Function.new(:void, [:int8, :int16])")

    def test_it_takes_a_DynamicLibrabry__Symbol_as_3_argument(self, ffi_space):
        ffi_space.execute("""
        dlsym = FFI::DynamicLibrary::Symbol.new(:fname)
        FFI::Function.new(:void, [:int8, :int16], dlsym)
        """)
        with self.raises(space, "TypeError",
                      "can't convert Fixnum into FFI::DynamicLibrary::Symbol"):
            space.execute("FFI::Function.new(:void, [:uint8], 500)")

    def test_it_takes_a_hash_as_4_argument(self, ffi_space):
        ffi_space.execute("""
        FFI::Function.new(:void, [:int8, :int16],
                          FFI::DynamicLibrary::Symbol.new('x'),
                          {})
        """)

    def test_it_understands_Type_constants_for_the_signature(self, ffi_space):
        ffi_space.execute("""
        FFI::Function.new(FFI::Type::VOID,
                          [FFI::Type::INT8, FFI::Type::INT16])
        """)

    def test_it_reacts_to_messy_signature_with_TypeError(self, ffi_space):
        with self.raises(ffi_space, "TypeError", "unable to resolve type '1'"):
            ffi_space.execute("FFI::Function.new(1, [])")
        with self.raises(ffi_space, "TypeError", "unable to resolve type '2'"):
            ffi_space.execute("FFI::Function.new(:void, [2])")
        with self.raises(ffi_space, "TypeError",
                         "unable to resolve type 'null'"):
            ffi_space.execute("FFI::Function.new(:null, [])")
        with self.raises(ffi_space, "TypeError",
                         "unable to resolve type 'array'"):
            ffi_space.execute("FFI::Function.new(:int32, [:array])")

    def test_it_creates_the_following_low_level_data(self, ffi_space):
        w_function = ffi_space.execute("""
        foo = FFI::DynamicLibrary::Symbol.new(:foo)
        FFI::Function.new(:int8, [:int16, :float64], foo, {})
        """)
        w_int16 = space.execute("FFI::Type::INT16")
        w_float64 = space.execute("FFI::Type::FLOAT64")
        w_int8 = space.execute("FFI::Type::INT8")
        assert w_function.arg_types_w == [w_int16, w_float64]
        assert w_function.w_ret_type == w_int8
        assert self.unwrap(space, w_function.w_name) == 'foo'

class TestFunction_attach(BaseFFITest):

    def make_mock_library_code(self, libname):
        return """
        module LibraryMock
            local = FFI::DynamicLibrary::RTLD_LOCAL
            @ffi_libs = [FFI::DynamicLibrary.open('%s', local)]
            @attachments = {}
            self.singleton_class.attr_reader :attachments
        end
        """ % libname

    def test_it_works_with_pow_from_libm(self, ffi_space):
        w_res = ffi_space.execute("""
        %s
        sym_pow = FFI::DynamicLibrary::Symbol.new(:pow)
        func = FFI::Function.new(:float64, [:float64, :float64], sym_pow, {})
        func.attach(LibraryMock, 'power')
        LibraryMock.attachments.include? :power
        (0..5).each.map { |x| LibraryMock.attachments[:power].call(x, 2) }
        """ % self.make_mock_library_code('libm.so'))
        assert self.unwrap(ffi_space, w_res) == [0.0, 1.0, 4.0, 9.0, 16.0, 25.0]

    def test_it_works_with_abs_from_libc(self, ffi_space):
        w_res = ffi_space.execute("""
        %s
        sym_abs = FFI::DynamicLibrary::Symbol.new(:abs)
        func = FFI::Function.new(:int32, [:int32], sym_abs, {})
        func.attach(LibraryMock, 'abs')
        LibraryMock.attachments.include? :abs
        (-3..+3).each.map { |x| LibraryMock.attachments[:abs].call(x) }
        """ % self.make_mock_library_code('libc.so.6'))
        res = [x.toint() for x in self.unwrap(ffi_space, w_res)]
        assert res == [3, 2, 1, 0, 1, 2, 3]
