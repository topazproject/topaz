from tests.base import BaseTopazTest
from topaz.objects.classobject import W_ClassObject

class TestFunction(BaseTopazTest):

    def test_basic(self, space):
        w_function = space.execute("FFI::Function")
        assert isinstance(w_function, W_ClassObject)
