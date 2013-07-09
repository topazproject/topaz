from tests.modules.ffi.base import BaseFFITest

class TestLibrary_method_missing(BaseFFITest):
    def test_it_has_a_look_at_attachments_before_raising_error(self, space):
        w_res = space.execute("""
        class IHaveCallMethod
          def call
            'bingo!'
          end
        end
        module FFI::Library
          Attachments = {:foo => IHaveCallMethod.new}
        end
        FFI::Library.foo
        """)
        assert self.unwrap(space, w_res) == 'bingo!'

    def test_it_raises_NoMethodError_if_attachments_lookup_fails(self, space):
        with self.raises(space, 'NoMethodError',
                         "undefined method `bar' for FFI::Library"):
            space.execute("""
            FFI::Library.bar
            """)

    #def test_it_runs_cabs(self, space):
    #    w_res = space.execute("""
    #    require 'ffi'

    #    module Foo
    #      extend FFI::Library
    #      ffi_lib FFI::Library::LIBC
    #      attach_function("cabs", "abs", [ :int ], :int)
    #    end
    #    Foo.cabs(-5)
    #    """)
    #    assert self.unwrap(space, w_res) == 5
