# coding=utf-8

from .base import BaseRuPyPyTest


class TestGlobals(BaseRuPyPyTest):
    def test_variables_readonly(self, space):
        for name in '$" $: $LOADED_FEATURES $LOAD_PATH'.split():
            with self.raises(space, "NameError"):
                space.execute("%s = ['a']" % name)
