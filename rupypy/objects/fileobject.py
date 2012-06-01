import os

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_FileObject(W_BaseObject):
    classdef = ClassDef("File", W_BaseObject.classdef)

    @classdef.singleton_method("dirname", path="path")
    def method_dirname(self, space, path):
        if "/" not in path:
            return space.newstr_fromstr(".")
        idx = path.rfind("/")
        while idx > 0 and path[idx - 1] == "/":
            idx -= 1
        if idx == 0:
            return space.newstr_fromstr("/")
        return space.newstr_fromstr(path[:idx])

    @classdef.singleton_method("expand_path", path="path", dir="path")
    def method_expand_path(self, space, path, dir=None):
        if path and path[0] == "~":
            if len(path) >= 2 and path[1] == "/":
                path = os.environ["HOME"] + path[1:]
            elif len(path) < 2:
                return space.newstr_fromstr(os.environ["HOME"])
            else:
                raise NotImplementedError
        elif not path or path[0] != "/":
            if dir is not None:
                dir = space.str_w(W_FileObject.method_expand_path(self, space, dir))
            else:
                dir = os.getcwd()

            path = dir + "/" + path

        items = []
        parts = path.split("/")
        for part in parts:
            if part == "..":
                items.pop()
            elif part and part != ".":
                items.append(part)

        if not items:
            return space.newstr_fromstr("/")
        return space.newstr_fromstr("/" + "/".join(items))
