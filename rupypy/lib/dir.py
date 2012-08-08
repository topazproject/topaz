import os

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object
from rupypy.objects.exceptionobject import W_SystemCallError
from rupypy.modules.enumerable import Enumerable


class W_Dir(W_Object):
    classdef = ClassDef("Dir", W_Object.classdef)
    classdef.include_module(Enumerable)

    @classdef.method("initialize", path="str")
    def method_initialize(self, space, path):
        msg = None
        if not os.path.exists(path):
            msg = "No such file or directory - %s" % path
        elif not os.path.isdir(path):
            msg = "Not a directory - %s" % path
        if msg:
            raise space.error(space.getclassfor(W_SystemCallError), msg)
        self.path = path

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_Dir(space)

    @classdef.singleton_method("pwd")
    def method_pwd(self, space):
        return space.newstr_fromstr(os.getcwd())

    @classdef.singleton_method("delete", path="path")
    def method_delete(self, space, path):
        try:
            os.rmdir(path)
        except OSError as e:
            raise space.error(space.getclassfor(W_SystemCallError), str(e))
        return space.newint(0)
