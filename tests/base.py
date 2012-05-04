from contextlib import contextmanager

import py

from rupypy.error import RubyError


class BaseRuPyPyTest(object):
    @contextmanager
    def raises(self, exc_name):
        with py.test.raises(RubyError) as exc:
            yield
        assert exc.value.w_value.classdef.name == exc_name