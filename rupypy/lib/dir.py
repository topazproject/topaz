import errno
import os

from rupypy.error import error_for_oserror
from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_Object
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.intobject import W_FixnumObject
from rupypy.utils import glob

def dir_glob(space, pattern, flag=0):
    if isinstance(pattern, W_ArrayObject):
        if not flag:
            res = []
            for each in space.listview(pattern):
                elem = glob.glob(space.str_w(each))
                if elem not in res:
                    res += elem
            return space.newarray(res)
        else:
            raise NotImplementedError, "No usage of flags supported."
    elif isinstance(pattern, W_StringObject):
        if not flag:
            return space.newarray(glob.glob(space.str_w(pattern)))
        else:
            raise NotImplementedError, "No usage of flags supported."
    else:
        raise space.error(space.w_TypeError,
            "can't convert %s into String" % pattern.classdef.name
        )        

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
        
    @classdef.singleton_method("glob")
    def method_glob(self, space, args_w):
        if len(args_w) > 1:
            # passed in additional flag
            if isinstance(args_w[1], W_FixnumObject):
                return dir_glob(space, args_w[0], space.w_int(args_w[1]))
            else:
                # invalid type of flag
                raise Exception, "Invalid type of flag"
        else:
            return dir_glob(space, args_w[0])
