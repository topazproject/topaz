import os

from rupypy.error import error_for_oserror
from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_Object
from rupypy.utils.ll_dir import opendir, readdir, closedir


class W_Dir(W_Object):
    classdef = ClassDef("Dir", W_Object.classdef, filepath=__file__)
    classdef.include_module(Enumerable)

    def __del__(self):
        if self.open:
            closedir(self.dirp)

    def ensure_open(self, space):
        if not self.open:
            raise space.error(space.w_IOError, "closed directory")

    @classdef.method("initialize", path="str")
    def method_initialize(self, space, path):
        self.path = path
        try:
            self.dirp = opendir(path)
        except OSError as e:
            raise error_for_oserror(space, e)
        self.open = True

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
        try:
            os.rmdir(path if path else "")
        except OSError as e:
            raise error_for_oserror(space, e)
        return space.newint(0)

    @classdef.method("read")
    def method_read(self, space, args_w):
        self.ensure_open(space)
        try:
            filename = readdir(self.dirp)
        except OSError as e:
            raise error_for_oserror(space, e)
        if filename is None:
            return space.w_nil
        else:
            return space.newstr_fromstr(filename)

    @classdef.method("close")
    def method_close(self, space):
        self.ensure_open(space)
        closedir(self.dirp)
        self.open = False
        return space.w_nil
