from tests.modules.ffi.base import BaseFFITest

class TestDataConverter(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::DataConverter.is_a? Module")

class TestDataConverter__native_type(BaseFFITest):
    def test_it_returns_nil_for_now(self, space):
        assert self.ask(space, "FFI::DataConverter.native_type(0).nil?")

def check_it_takes_two_args_and_returns_the_first(ffitest, space, funcname):
    w_res = space.execute("%s(1, 2)" %funcname)
    assert ffitest.unwrap(space, w_res) == 1
    with ffitest.raises(space, "ArgumentError"):
        space.execute(funcname)
    with ffitest.raises(space, "ArgumentError"):
        space.execute("%s(1)" %funcname)
    with ffitest.raises(space, "ArgumentError"):
        space.execute("%s(1, 2, 3)" %funcname)

class TestDataConverter__to_native(BaseFFITest):
    def test_it_takes_two_arguments_and_returns_the_first_one(self, space):
        check_it_takes_two_args_and_returns_the_first(self, space,
                                                      "FFI::DataConverter.to_native")

class TestDataConverter__from_native(BaseFFITest):
    def test_it_returns_nil_for_now(self, space):
        check_it_takes_two_args_and_returns_the_first(self, space,
                                                      "FFI::DataConverter.from_native")
