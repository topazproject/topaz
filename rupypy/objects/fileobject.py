import os
import sys

from pypy.rlib.streamio import fdopen_as_stream, open_file_as_stream

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.hashobject import W_HashObject
from rupypy.objects.intobject import W_FixnumObject
from rupypy.objects.exceptionobject import W_ArgumentError


class W_IOObject(W_Object):
    classdef = ClassDef("IO", W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.fd = -1
        self.stream = None

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_IOObject(space)

    @classdef.method("initialize")
    def method_initialize(self, space, w_fd_or_io, w_mode_str_or_int=None, w_opts=None):
        if isinstance(w_fd_or_io, W_IOObject):
            fd = w_fd_or_io.fd
        else:
            fd = space.int_w(w_fd_or_io)
        if isinstance(w_mode_str_or_int, W_StringObject):
            mode = space.str_w(w_mode_str_or_int)
            if ":" in mode:
                raise NotImplementedError("encoding for IO.new")
        elif w_mode_str_or_int is None:
            mode = None
        else:
            raise NotImplementedError("int mode for IO.new")
        if w_opts is not None:
            raise NotImplementedError("options hash for IO.new")
        if mode is None:
            mode = "r"
        self.stream = fdopen_as_stream(fd, "r")
        self.fd = fd
        return self

    @classdef.method("read")
    def method_read(self, space, w_length=None, w_str=None):
        if w_length is None:
            return space.newstr_fromstr(str(self.stream.read(-1)))
        length = space.int_w(w_length)
        if length < 0:
            space.raise_(space.getclassfor(W_ArgumentError), "negative length %d given" % length)
        read_bytes = ""
        while len(read_bytes) < length:
            current_read = self.stream.read(length - len(read_bytes))
            read_bytes += current_read
            if len(current_read) == 0:
                break
        # Return nil on EOF if length is given
        if len(read_bytes) == 0:
            return space.w_nil
        read_str = space.newstr_fromstr(read_bytes)
        if w_str is not None:
            w_str.method_clear(space)
            w_str.method_lshift(space, read_str)
            return w_str
        else:
            return read_str

    @classdef.method("write")
    def method_write(self, space, w_str):
        old_pos = self.stream.tell()
        assert isinstance(old_pos, int)
        string = space.str_w(space.send(w_str, space.newsymbol("to_s")))
        self.stream.write(string)
        new_pos = self.stream.tell()
        assert isinstance(new_pos, int)
        return space.newint(new_pos - old_pos)


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
        space.set_const(w_cls, "ALT_SEPARATOR", w_alt_seperator)
        space.set_const(w_cls, "FNM_SYSCASE", w_fnm_syscase)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_FileObject(space)

    @classdef.method("initialize", filename="str")
    def method_initialize(self, space, filename, w_mode=None, w_perm_or_opt=None, w_opt=None):
        if isinstance(w_perm_or_opt, W_HashObject):
            assert w_opt is None
            perm = 665
            w_opt = w_perm_or_opt
        elif w_opt is not None:
            assert isinstance(w_perm_or_opt, W_FixnumObject)
            perm = space.int_w(w_perm_or_opt)
        else:
            perm = 665
        if w_mode is None:
            mode = "r"
        elif isinstance(w_mode, W_StringObject):
            mode = space.str_w(w_mode)
        else:
            raise NotImplementedError("int mode for File.new")
        if w_perm_or_opt is not None or w_opt is not None:
            raise NotImplementedError("options hash or permissions for File.new")
        self.stream = open_file_as_stream(filename, mode)
        self.fd = self.stream.try_to_find_file_descriptor()
        return self

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
