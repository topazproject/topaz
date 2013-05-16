from tests.base import BaseTopazTest
from topaz.objects.moduleobject import W_ModuleObject

class TestDataConverter(BaseTopazTest):

    def test_is_module(self, space):
        w_dc = space.execute('FFI::DataConverter')
        assert isinstance(w_dc, W_ModuleObject)

    def test_native_type(self, space):
        w_res = space.execute('FFI::DataConverter.native_type(0)')
        assert w_res == space.w_nil

    def test_to_native(self, space):
        w_res = space.execute('FFI::DataConverter.to_native')
        assert w_res == space.w_nil

    def test_from_native(self, space):
        w_res = space.execute('FFI::DataConverter.from_native')
        assert w_res == space.w_nil
