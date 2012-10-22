# coding=utf-8

from .base import BaseRuPyPyTest


class TestObjectSpace(BaseRuPyPyTest):
    def test_convert_type(self, space):
        assert space.convert_type(space.newint(3), space.w_array, 'to_ary', False) is space.w_nil
        with self.raises(space, "TypeError"):
            space.convert_type(space.newint(3), space.w_array, 'to_ary')
