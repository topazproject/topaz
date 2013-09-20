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

    def test_it_takes_a_DynamicLibrabry__Symbol_as_3rd_argument(self, ffis):
        ffis.execute("""
        dlsym = FFI::DynamicLibrary.open('libm.so').find_function(:sin)
        FFI::Function.new(:void, [:int8, :int16], dlsym)
        """)
        with self.raises(ffis, "TypeError",
                      "can't convert Fixnum into FFI::DynamicLibrary::Symbol"):
            ffis.execute("FFI::Function.new(:void, [:uint8], 500)")

    def test_it_takes_a_hash_as_4_argument(self, ffis):
        ffis.execute("""
        FFI::Function.new(:void, [:int8, :int16],
                          FFI::DynamicLibrary.open('libm.so').find_function(:cos),
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
        tan = FFI::DynamicLibrary.open('libm.so').find_function(:tan)
        FFI::Function.new(:float64, [:float64], tan, {})
        """)
        w_float64 = ffis.execute("FFI::Type::FLOAT64")
        assert w_function.arg_types_w == [w_float64]
        assert w_function.w_ret_type == w_float64
        tan = clibffi.CDLL('libm.so').getpointer('tan',
                                                 [clibffi.ffi_type_double],
                                                 clibffi.ffi_type_double)
        assert w_function.ptr == tan.funcsym

class TestFunction_attach(BaseFFITest):

    def make_mock_library_code(self, libname):
        return """
        module LibraryMock
            local = FFI::DynamicLibrary::RTLD_LOCAL
            @ffi_libs = [FFI::DynamicLibrary.open('%s', local)]
            @attachments = {}
            self.singleton_class.attr_reader :attachments

            def self.find_function(name)
                @ffi_libs[0].find_function(name)
            end
        end
        """ % libname

    def test_it_works_with_pow_from_libm(self, ffis):
        w_res = ffis.execute("""
        %s
        sym_pow = LibraryMock.find_function(:pow)
        func = FFI::Function.new(:float64, [:float64, :float64], sym_pow, {})
        func.attach(LibraryMock, 'power')
        LibraryMock.attachments.include? :power
        (0..5).each.map { |x| LibraryMock.attachments[:power].call(x, 2) }
        """ % self.make_mock_library_code('libm.so'))
        assert self.unwrap(ffis, w_res) == [0.0, 1.0, 4.0, 9.0, 16.0, 25.0]

    def test_it_works_with_abs_from_libc(self, ffis):
        w_res = ffis.execute("""
        %s
        sym_abs = LibraryMock.find_function(:abs)
        func = FFI::Function.new(:int32, [:int32], sym_abs, {})
        func.attach(LibraryMock, 'abs')
        LibraryMock.attachments.include? :abs
        (-3..+3).each.map { |x| LibraryMock.attachments[:abs].call(x) }
        """ % self.make_mock_library_code('libc.so.6'))
        assert self.unwrap(ffis, w_res) == [3, 2, 1, 0, 1, 2, 3]

    def test_it_works_with_strings(self, ffis):
        w_res = ffis.execute("""
        %s
        sym_strcat = LibraryMock.find_function(:strcat)
        func = FFI::Function.new(:string, [:string, :string], sym_strcat, {})
        func.attach(LibraryMock, 'strcat')
        LibraryMock.attachments[:strcat].call("Well ", "done!")
        """ % self.make_mock_library_code('libc.so.6'))
        assert self.unwrap(ffis, w_res) == "Well done!"

    def test_it_works_with_float(self, ffis, libtest_so):
        w_res = ffis.execute("""
        %s
        sym_add_float = LibraryMock.find_function(:add_float)
        func = FFI::Function.new(:float32, [:float32, :float32], sym_add_float, {})
        func.attach(LibraryMock, 'add_float')
        LibraryMock.attachments[:add_float].call(1.5, 2.25)
        """ % self.make_mock_library_code(libtest_so))
        assert self.unwrap(ffis, w_res) == 3.75

    def make_question_code(self, signchar, size, left=1, right=2,
                           with_name=None):
        default_T = '%sint%s' %('' if signchar == 's' else 'u', size)
        T = default_T if with_name is None else with_name
        fn = 'add_%s%s' %(signchar, size)
        plus_or_minus = '-' if signchar == 's' else '+'
        return ("""
        FFI::Function.new(:T, [:T, :T],
                          LibraryMock.find_function(:fn),
                          {}).attach(LibraryMock, 'fn')
        LibraryMock.attachments[:fn].call(+|-%s, +|-%s) == +|-%s
        """.replace('T', T).replace('fn', fn).replace('+|-', plus_or_minus) %
        (left, right, left+right))

    def type_works(self, ffis, libtest_so, typechar, size, left=1, right=2,
                   with_name=None):
        return self.ask(ffis,
                        self.make_mock_library_code(libtest_so) +
                        self.make_question_code(typechar, size, left, right,
                                                with_name))

    def test_it_works_with_unsigned_int8(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 'u', '8')

    def test_it_works_with_signed_int8(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 's', '8')

    def test_it_works_with_unsigned_int16(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 'u', '16')

    def test_it_works_with_signed_int16(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 's', '16')

    def test_it_works_with_unsigned_shorts(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 'u', '16', with_name='short')

    def test_it_works_with_signed_shorts(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 's', '16', with_name='short')

    def test_it_works_with_unsigned_int32(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 'u', '32')

    def test_it_works_with_signed_int32(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 's', '32')

    def test_it_works_with_unsigned_ints(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 'u', '32', with_name='int')

    def test_it_works_with_signed_ints(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 's', '32', with_name='int')

    def test_it_works_with_unsigned_int64(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 'u', '64', 2**61, 2**61)

    def test_it_works_with_signed_int64(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 's', '64', 2**61, 2**61)

    def test_it_works_with_unsigned_long_longs(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 'u', '64', 2**61, 2**61,
                               with_name='long_long')

    def test_it_works_with_signed_long_longs(self, ffis, libtest_so):
        assert self.type_works(ffis, libtest_so, 's', '64', 2**61, 2**61,
                               with_name='long_long')

    def test_it_works_with_long(self, ffis, libtest_so):
        w_res = ffis.execute("""
        %s
        sym_add_long = LibraryMock.find_function(:add_long)
        func = FFI::Function.new(:long, [:long, :long], sym_add_long, {})
        func.attach(LibraryMock, 'add_long')
        LibraryMock.attachments[:add_long].call(-2, -10)
        """ % self.make_mock_library_code(libtest_so))
        res = self.unwrap(ffis, w_res)
        assert (res == -12 if isinstance(res, int) else res.toint() == -12)

    def test_it_works_with_ulong(self, ffis, libtest_so):
        w_res = ffis.execute("""
        %s
        sym_add_ulong = LibraryMock.find_function(:add_ulong)
        func = FFI::Function.new(:ulong, [:ulong, :ulong], sym_add_ulong, {})
        func.attach(LibraryMock, 'add_ulong')
        LibraryMock.attachments[:add_ulong].call(2, 10)
        """ % self.make_mock_library_code(libtest_so))
        res = self.unwrap(ffis, w_res)
        assert (res == 12 if isinstance(res, int) else res.toint() == 12)

    def test_it_returns_nil_for_void(self, ffis, libtest_so):
        w_res = ffis.execute("""
        %s
        FFI::Function.new(:void, [:uint8],
                          LibraryMock.find_function(:set_u8),
                          {}).attach(LibraryMock, 'do_nothing')
        LibraryMock.attachments[:do_nothing].call(0)
        """ % self.make_mock_library_code(libtest_so))
        assert w_res is ffis.w_nil

    def test_it_works_with_bools(self, ffis, libtest_so):
        ffis.execute("""
        %s
        FFI::Function.new(:bool, [:bool],
                          LibraryMock.find_function(:bool_reverse_val),
                          {}).attach(LibraryMock, 'not')
        """ % self.make_mock_library_code(libtest_so))
        w_res = ffis.execute("LibraryMock.attachments[:not].call(true)")
        assert w_res is ffis.w_false
        w_res = ffis.execute("LibraryMock.attachments[:not].call(false)")
        assert w_res is ffis.w_true

    def test_it_can_convert_nil_to_NULL(self, ffis, libtest_so):
        self.ask(ffis, """
        %s
        FFI::Function.new(:bool, [:pointer],
                          LibraryMock.find_function(:testIsNULL),
                          {}).attach(LibraryMock, 'test_is_NULL')
        LibraryMock.attachments[:test_is_NULL].call(nil)
        """ % self.make_mock_library_code(libtest_so))

    def test_it_works_with_pointer_argument(self, ffis, libtest_so):
        w_res = ffis.execute("""
        %s
        FFI::Function.new(:void, [:int, :int, :pointer],
                          LibraryMock.find_function(:ref_add_int32_t),
                          {}).attach(LibraryMock, 'add')
        res = FFI::MemoryPointer.new(:int, 1)
        LibraryMock.attachments[:add].call(4, 6, res)
        res.read_int32
        """ % self.make_mock_library_code(libtest_so))
        assert self.unwrap(ffis, w_res) == 10

    def test_it_returns_pointer_object(self, ffis, libtest_so):
        ffis.execute("""
        %s
        FFI::Function.new(:pointer, [:int],
                          LibraryMock.find_function(:ptr_malloc),
                          {}).attach(LibraryMock, 'malloc')
        """ % self.make_mock_library_code(libtest_so))
        assert self.ask(ffis, """
        LibraryMock.attachments[:malloc].call(8).kind_of?(FFI::Pointer)
        """)
