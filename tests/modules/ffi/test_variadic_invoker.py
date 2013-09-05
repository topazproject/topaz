from tests.modules.ffi.base import BaseFFITest

class TestVariadicInvoker(BaseFFITest):
    def test_it_is_not_a_function(self, ffis):
        assert self.ask(ffis, "! FFI::VariadicInvoker.kind_of? FFI::Function")

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
            @ffi_libs = [FFI::DynamicLibrary.open('libc.so.6', local)]
        end
        sym_printf = FFI::DynamicLibrary::Symbol.new('printf')
        printf = FFI::VariadicInvoker.new(sym_printf,
                                          [FFI::Type::STRING],
                                          FFI::Type::INT32)
        printf.attach(Lib, :printf)
        Lib.printf("%i, %f, %s", :int32, 1, :float, 2.0, :string, 'three')
        """)
        assert self.unwrap(ffis, w_res) == "1, 2.0, three"
