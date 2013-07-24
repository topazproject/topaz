from tests.modules.ffi.base import BaseFFITest
from topaz.objects.classobject import W_ClassObject
from topaz.modules.ffi.function import W_FunctionObject
from topaz.modules.ffi.type import ffi_types, aliases

from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

import os

libm = clibffi.CDLL('libm.so')

class TestFunction(BaseFFITest):

    def test_it_has_FFI_Pointer_as_ancestor(self, space):
        assert self.ask(space, "FFI::Function.ancestors.include? FFI::Pointer")

class TestFunction__new(BaseFFITest):

    def test_it_needs_at_least_a_type_signature(self, ffis):
        ffis.execute("FFI::Function.new(:void, [:int8, :int16])")

    def test_it_takes_a_DynamicLibrabry__Symbol_as_3_argument(self, ffis):
        ffis.execute("""
        dlsym = FFI::DynamicLibrary::Symbol.new(:fname)
        FFI::Function.new(:void, [:int8, :int16], dlsym)
        """)
        with self.raises(ffis, "TypeError",
                      "can't convert Fixnum into FFI::DynamicLibrary::Symbol"):
            ffis.execute("FFI::Function.new(:void, [:uint8], 500)")

    def test_it_takes_a_hash_as_4_argument(self, ffis):
        ffis.execute("""
        FFI::Function.new(:void, [:int8, :int16],
                          FFI::DynamicLibrary::Symbol.new('x'),
                          {})
        """)

    def test_it_understands_Type_constants_for_the_signature(self, ffis):
        ffis.execute("""
        FFI::Function.new(FFI::Type::VOID,
                          [FFI::Type::INT8, FFI::Type::INT16])
        """)

    def test_it_reacts_to_messy_signature_with_TypeError(self, ffis):
        with self.raises(ffis, "TypeError", "unable to resolve type '1'"):
            ffis.execute("FFI::Function.new(1, [])")
        with self.raises(ffis, "TypeError", "unable to resolve type '2'"):
            ffis.execute("FFI::Function.new(:void, [2])")
        with self.raises(ffis, "TypeError",
                         "unable to resolve type 'null'"):
            ffis.execute("FFI::Function.new(:null, [])")
        with self.raises(ffis, "TypeError",
                         "unable to resolve type 'array'"):
            ffis.execute("FFI::Function.new(:int32, [:array])")

    def test_it_creates_the_following_low_level_data(self, ffis):
        w_function = ffis.execute("""
        foo = FFI::DynamicLibrary::Symbol.new(:foo)
        FFI::Function.new(:int8, [:int16, :float64], foo, {})
        """)
        w_int16 = ffis.execute("FFI::Type::INT16")
        w_float64 = ffis.execute("FFI::Type::FLOAT64")
        w_int8 = ffis.execute("FFI::Type::INT8")
        assert w_function.arg_types_w == [w_int16, w_float64]
        assert w_function.w_ret_type == w_int8
        assert self.unwrap(ffis, w_function.w_name) == 'foo'

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

    def test_it_works_with_pow_from_libm(self, ffis):
        w_res = ffis.execute("""
        %s
        sym_pow = FFI::DynamicLibrary::Symbol.new(:pow)
        func = FFI::Function.new(:float64, [:float64, :float64], sym_pow, {})
        func.attach(LibraryMock, 'power')
        LibraryMock.attachments.include? :power
        (0..5).each.map { |x| LibraryMock.attachments[:power].call(x, 2) }
        """ % self.make_mock_library_code('libm.so'))
        assert self.unwrap(ffis, w_res) == [0.0, 1.0, 4.0, 9.0, 16.0, 25.0]

    def test_it_works_with_abs_from_libc(self, ffis):
        w_res = ffis.execute("""
        %s
        sym_abs = FFI::DynamicLibrary::Symbol.new(:abs)
        func = FFI::Function.new(:int32, [:int32], sym_abs, {})
        func.attach(LibraryMock, 'abs')
        LibraryMock.attachments.include? :abs
        (-3..+3).each.map { |x| LibraryMock.attachments[:abs].call(x) }
        """ % self.make_mock_library_code('libc.so.6'))
        res = [x.toint() for x in self.unwrap(ffis, w_res)]
        assert res == [3, 2, 1, 0, 1, 2, 3]

    def test_it_works_with_strings(self, ffis):
        w_res = ffis.execute("""
        %s
        sym_strcat = FFI::DynamicLibrary::Symbol.new(:strcat)
        func = FFI::Function.new(:string, [:string, :string], sym_strcat, {})
        func.attach(LibraryMock, 'strcat')
        LibraryMock.attachments[:strcat].call("Well ", "done!")
        """ % self.make_mock_library_code('libc.so.6'))
        assert self.unwrap(ffis, w_res) == "Well done!"

    def test_it_works_with_shorts(self, ffis, libtest_so):
        w_res = ffis.execute("""
        %s
        sym_add_u16 = FFI::DynamicLibrary::Symbol.new(:add_u16)
        func = FFI::Function.new(:uint16, [:uint16, :uint16], sym_add_u16, {})
        func.attach(LibraryMock, 'add_u16')
        LibraryMock.attachments[:add_u16].call(1, 2)
        """ % self.make_mock_library_code(libtest_so))
        assert self.unwrap(ffis, w_res).toint() == 3
