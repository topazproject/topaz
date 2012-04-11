from rupypy.objects.intobject import W_IntObject


class TestObjectObject(object):
    def test_class(self, space):
        w_res = space.execute("return 1.class")
        assert w_res is space.getclassobject(W_IntObject.classdef)
