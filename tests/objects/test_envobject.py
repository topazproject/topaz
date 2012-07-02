from rupypy.objects.objectobject import W_Object

from ..base import BaseRuPyPyTest


class TestEnvObject(BaseRuPyPyTest):
    def test_class(self, space):
        w_res = space.execute("return ENV.class")
        assert w_res == self.find_const(space, "Object")
