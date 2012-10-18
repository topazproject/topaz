# coding=utf-8

from rupypy.objects.arrayobject import W_ArrayObject

from .base import BaseRuPyPyTest


class TestObjectSpace(BaseRuPyPyTest):
    def test_convert_type(self, space):
        assert space.convert_type(space.newint(3), space.getclassfor(W_ArrayObject), 'to_ary', False) == space.w_nil
        with self.raises(space, "TypeError"):
            space.convert_type(space.newint(3), space.getclassfor(W_ArrayObject), 'to_ary')
