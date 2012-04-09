from rupypy.objects.objectobject import W_Object


class W_ClassObject(W_Object):
    def __init__(self, name):
        self.name = name
        self.methods_w = {}

    def add_method(self, name, method):
        self.methods_w[name] = method

    def find_method(self, space, method):
        return self.methods_w[method]