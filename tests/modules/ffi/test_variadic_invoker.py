from tests.modules.ffi.base import BaseFFITest
import sys

if sys.platform == 'darwin':
    libc = 'libc.dylib'
else:
    libc = 'libc.so.6'

class TestVariadicInvoker(BaseFFITest):
    def test_it_is_not_a_function(self, space):
        assert self.ask(space, "! FFI::VariadicInvoker.kind_of? FFI::Function")

    def test_it_still_can_be_attached_and_called(self, ffis):
        assert self.ask(ffis, """
        [:attach, :call].all? do |methodname|
          FFI::VariadicInvoker.instance_methods.include? methodname
        end
        """)

    def test_it_still_can_be_used_like_a_function(self, ffis):
        w_res = ffis.execute("""
        module Lib
            local = FFI::DynamicLibrary::RTLD_LOCAL
            @ffi_libs = [FFI::DynamicLibrary.open('%(libname)s', local)]
        end
        libc = FFI::DynamicLibrary.new('%(libname)s')
        sym_sprintf = libc.find_function(:sprintf)
        sprintf = FFI::VariadicInvoker.new(sym_sprintf,
                                           [FFI::Type::POINTER, FFI::Type::STRING],
                                           FFI::Type::INT32)
        sprintf.attach(Lib, :sprintf)
        result = FFI::MemoryPointer.new(:int8, 14)
        Lib.sprintf(result, "%%i, %%f", FFI::Type::INT32, 1,
                                        FFI::Type::FLOAT64, 2.0)
        chars = 0.upto(5).map { |x| result.get_int8(x).chr }
        chars.inject('') { |str, c| str << c }
        """ % {'libname':libc})
        assert self.unwrap(ffis, w_res) == "1, 2.0"
        w_res = ffis.execute("""
        result = FFI::MemoryPointer.new(:int8, 14)
        Lib.sprintf(result, "%%i, %%f", FFI::Type::INT32, 3,
                                        FFI::Type::FLOAT64, 4.0)
        """)
        assert self.unwrap(ffis, w_res) == 6

    def test_it_also_is_able_to_use_typedefs(self, ffis):
        w_res = ffis.execute("""
        module Lib
            local = FFI::DynamicLibrary::RTLD_LOCAL
            @ffi_libs = [FFI::DynamicLibrary.open('%(libname)s', local)]
        end
        libc = FFI::DynamicLibrary.new('%(libname)s')
        sym_sprintf = libc.find_function(:sprintf)
        options = {:type_map => {:name => FFI::Type::STRING}}
        sprintf = FFI::VariadicInvoker.new(sym_sprintf,
                                           [FFI::Type::POINTER,
                                            FFI::Type::STRING],
                                           FFI::Type::INT32,
                                           options)
        sprintf.attach(Lib, :sprintf)
        result = FFI::MemoryPointer.new(:int8, 25)
        Lib.sprintf(result, "%%s is father of %%s",
                    :name, "bill", :name, "johanna")
        chars = 0.upto(24).map { |x| result.get_int8(x).chr }
        chars.inject('') { |str, c| str << c }
        """ % {'libname':libc})
        assert self.unwrap(ffis, w_res) == "bill is father of johanna"
