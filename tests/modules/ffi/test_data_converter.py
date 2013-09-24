from tests.modules.ffi.base import BaseFFITest

class TestDataConverter(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::DataConverter.is_a? Module")

class TestDataConverter__native_type(BaseFFITest):
    def test_it_returns_nil_for_now(self, space):
        assert self.ask(space, "FFI::DataConverter.native_type(0).nil?")

class TestDataConverter__to_native(BaseFFITest):
    def test_it_returns_nil_for_now(self, space):
        assert self.ask(space, "FFI::DataConverter.to_native.nil?")

class TestDataConverter__from_native(BaseFFITest):
    def test_it_returns_nil_for_now(self, space):
        assert self.ask(space, "FFI::DataConverter.from_native.nil?")
