import errno
import os

from rupypy.error import error_for_oserror
from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_Object


class W_Dir(W_Object):
    classdef = ClassDef("Dir", W_Object.classdef)
    classdef.include_module(Enumerable)

    @classdef.method("initialize", path="str")
    def method_initialize(self, space, path):
        msg = None
        if not os.path.exists(path):
            msg = "No such file or directory - %s" % path
            w_errno = space.newint(errno.ENOENT)
        elif not os.path.isdir(path):
            msg = "Not a directory - %s" % path
            w_errno = space.newint(errno.ENOTDIR)
        if msg:
            raise space.error(space.w_SystemCallError, msg, [w_errno])
        self.path = path
        self.iterator = iter(os.listdir(self.path))

    @classdef.method("close")
    def method_close(self, space):
        return self

    @classdef.method("path")
    def method_path(self, space):
        return space.newstr_fromstr(self.path)

    @classdef.method("read")
    def method_read(self, space):
        try:
            return space.newstr_fromstr(self.iterator.next())
        except StopIteration:
            return space.w_nil

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_Dir(space)

    @classdef.singleton_method("pwd")
    def method_pwd(self, space):
        return space.newstr_fromstr(os.getcwd())

    @classdef.singleton_method("delete", path="path")
    def method_delete(self, space, path):
        assert path
        try:
            os.rmdir(path)
        except OSError as e:
            raise error_for_oserror(space, e)
        return space.newint(0)
