import os
import sys

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object
from rupypy.objects.arrayobject import W_ArrayObject


class W_IOObject(W_Object):
    classdef = ClassDef("IO", W_Object.classdef)


class W_FileObject(W_IOObject):
    classdef = ClassDef("File", W_IOObject.classdef)

    @classmethod
    def setup_class(cls, space, w_cls):
        super(W_FileObject, cls).setup_class(space, w_cls)
        if sys.platform == "win32":
            w_alt_seperator = space.newstr_fromstr("\\")
            w_fnm_syscase = space.newint(0x08)
        else:
            w_alt_seperator = space.w_nil
            w_fnm_syscase = space.newint(0)
        space.set_const(w_cls, "SEPARATOR", space.newstr_fromstr("/"))
        space.set_const(w_cls, "ALT_SEPARATOR", w_alt_seperator)
        space.set_const(w_cls, "FNM_SYSCASE", w_fnm_syscase)

    @classdef.singleton_method("dirname", path="path")
    def method_dirname(self, space, path):
        if "/" not in path:
            return space.newstr_fromstr(".")
        idx = path.rfind("/")
        while idx > 0 and path[idx - 1] == "/":
            idx -= 1
        if idx == 0:
            return space.newstr_fromstr("/")
        assert idx >= 0
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

    @classdef.singleton_method("join")
    def singleton_method_join(self, space, args_w):
        sep = space.str_w(space.find_const(self, "SEPARATOR"))
        result = ""
        for w_arg in args_w:
            if isinstance(w_arg, W_ArrayObject):
                string = space.str_w(
                    W_FileObject.singleton_method_join(self, space, space.listview(w_arg))
                )
            else:
                string = space.str_w(w_arg)
            if string.startswith(sep):
                result = result.rstrip(sep)
            elif result and not result.endswith(sep):
                result += sep
            result += string
        return space.newstr_fromstr(result)
