import os

from topaz.error import error_for_oserror
from topaz.module import ClassDef
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object
from topaz.objects.regexpobject import RegexpCache
from topaz.utils.glob import Glob
from topaz.utils.ll_dir import opendir, readdir, closedir


class W_DirObject(W_Object):
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
        return W_DirObject(space)

    @classdef.singleton_method("pwd")
    @classdef.singleton_method("getwd")
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

    @classdef.singleton_method("[]")
    def method_subscript(self, space, args_w):
        if len(args_w) == 1:
            return space.send(self, space.newsymbol("glob"), args_w)
        else:
            return space.send(self, space.newsymbol("glob"), [space.newarray(args_w)])

    @classdef.singleton_method("glob", flags="int")
    def method_glob(self, space, w_pattern, flags=0, block=None):
        if space.is_kind_of(w_pattern, space.w_array):
            patterns_w = space.listview(w_pattern)
        else:
            patterns_w = [w_pattern]

        glob = Glob(space.fromcache(RegexpCache))

        for w_pat in patterns_w:
            if space.is_kind_of(w_pat, space.w_string):
                pattern = space.str_w(w_pat)
            else:
                pattern = space.str_w(space.convert_type(w_pat, space.w_string, "to_str"))
            if len(patterns_w) == 1:
                for pat in pattern.split("\0"):
                    glob.glob(pat, flags)
            else:
                glob.glob(pattern, flags)

        if block:
            for match in glob.matches():
                space.invoke_block(block, [space.newstr_fromstr(match)])
            return space.w_nil
        else:
            return space.newarray([space.newstr_fromstr(s) for s in glob.matches()])

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
