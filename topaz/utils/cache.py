from rpython.rlib.objectmodel import specialize


class Cache(object):
    def __init__(self, space):
        self.space = space
        self.contents = {}

    @specialize.memo()
    def getorbuild(self, key):
        try:
            return self.contents[key]
        except KeyError:
            builder = self._build(key)
            self.contents[key] = builder.next()
            try:
                builder.next()
            except StopIteration:
                pass
            else:
                raise RuntimeError("generator didn't stop")
            return self.contents[key]

    def _freeze_(self):
        return True
