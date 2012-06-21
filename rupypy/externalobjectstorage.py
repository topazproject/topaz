from pypy.rlib import jit

class ExternalValue(object):
    def __init__(self, default):
        self.w_value = default

class ExternalValues(object):
    def __init__(self):
        self.values = {}

    @jit.elidable
    def _get_value(self, object_key, default):
        return self.values.setdefault(object_key, ExternalValue(default))

class ExternalObjectStorage(object):
    def __init__(self):
        self.storage = {}

    def get(self, space, value_key, object_key, default):
        return self._get_list(value_key)._get_value(object_key, default).w_value

    def set(self, space, value_key, object_key, w_value):
        self._get_list(value_key)._get_value(object_key, None).w_value = w_value

    @jit.elidable
    def _get_list(self, value_key):
        return self.storage.setdefault(value_key, ExternalValues())
