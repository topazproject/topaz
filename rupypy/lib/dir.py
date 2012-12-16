import errno
import os

from rupypy.error import error_for_oserror
from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_Object


class W_Dir(W_Object):
    classdef = ClassDef("Dir", W_Object.classdef, filepath=__file__)
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

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_Dir(space)

    @classdef.singleton_method("pwd")
    def method_pwd(self, space):
        return space.newstr_fromstr(os.getcwd())

    @classdef.singleton_method("chdir", path="path")
    def method_chdir(self, space, path=None, block=None):
        if path is None:
            path = os.environ["HOME"]
        current_dir = os.getcwd()
        os.chdir(path)
        if block is not None:
            try:
                return space.invoke_block(block, [space.newstr_fromstr(path)])
            finally:
                os.chdir(current_dir)
        else:
            return space.newint(0)

    @classdef.singleton_method("delete", path="path")
    def method_delete(self, space, path):
        assert path
        try:
            os.rmdir(path)
        except OSError as e:
            raise error_for_oserror(space, e)
        return space.newint(0)
