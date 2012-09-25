import os
import sys

from rupypy.module import ClassDef
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.exceptionobject import W_ArgumentError
from rupypy.objects.hashobject import W_HashObject
from rupypy.objects.objectobject import W_Object
from rupypy.objects.stringobject import W_StringObject


class W_IOObject(W_Object):
    classdef = ClassDef("IO", W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.fd = -1

    def __del__(self):
        # Do not close standard file streams
        if self.fd > 3:
            os.close(self.fd)

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
        self.fd = fd
        return self

    @classdef.method("read")
    def method_read(self, space, w_length=None, w_str=None):
        if w_length:
            length = space.int_w(w_length)
            if length < 0:
                raise space.error(
                    space.getclassfor(W_ArgumentError), "negative length %d given" % length
                )
        else:
            length = -1
        read_bytes = 0
        read_chunks = []
        while length < 0 or read_bytes < length:
            if length > 0:
                max_read = int(length - read_bytes)
            else:
                max_read = 8192
            current_read = os.read(self.fd, max_read)
            if len(current_read) == 0:
                break
            read_bytes += len(current_read)
            read_chunks += current_read
        # Return nil on EOF if length is given
        if read_bytes == 0:
            return space.w_nil
        w_read_str = space.newstr_fromchars(read_chunks)
        if w_str is not None:
            w_str.clear(space)
            w_str.extend(space, w_read_str)
            return w_str
        else:
            return w_read_str

    @classdef.method("write")
    def method_write(self, space, w_str):
        string = space.str_w(space.send(w_str, space.newsymbol("to_s")))
        bytes_written = os.write(self.fd, string)
        return space.newint(bytes_written)

    @classdef.method("print")
    def method_print(self, space, args_w):
        if not args_w:
            w_last = space.globals.get("$_")
            if w_last:
                args_w.append(w_last)
        w_sep = space.globals.get("$,")
        if w_sep:
            sep = space.str_w(w_sep)
        else:
            sep = ""
        w_end = space.globals.get("$\\")
        if w_end:
            end = space.str_w(w_end)
        else:
            end = ""
        strings = [space.str_w(space.send(w_arg, space.newsymbol("to_s"))) for w_arg in args_w]
        os.write(self.fd, sep.join(strings))
        os.write(self.fd, end)
        return space.w_nil

    @classdef.method("puts")
    def method_puts(self, space, args_w):
        for w_arg in args_w:
            string = space.str_w(space.send(w_arg, space.newsymbol("to_s")))
            os.write(self.fd, string)
            if not string.endswith("\n"):
                os.write(self.fd, "\n")
        return space.w_nil


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
        space.set_const(w_cls, "RDONLY", space.newint(os.O_RDONLY))
        space.set_const(w_cls, "WRONLY", space.newint(os.O_WRONLY))
        space.set_const(w_cls, "RDWR", space.newint(os.O_RDWR))
        space.set_const(w_cls, "APPEND", space.newint(os.O_APPEND))
        space.set_const(w_cls, "CREAT", space.newint(os.O_CREAT))
        space.set_const(w_cls, "EXCL", space.newint(os.O_EXCL))
        space.set_const(w_cls, "TRUNC", space.newint(os.O_TRUNC))

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_FileObject(space)

    @classdef.method("initialize", filename="str")
    def method_initialize(self, space, filename, w_mode=None, w_perm_or_opt=None, w_opt=None):
        if isinstance(w_perm_or_opt, W_HashObject):
            assert w_opt is None
            perm = 0665
            w_opt = w_perm_or_opt
        elif w_opt is not None:
            perm = space.int_w(w_perm_or_opt)
        else:
            perm = 0665
        if w_mode is None:
            mode = os.O_RDONLY
        elif isinstance(w_mode, W_StringObject):
            mode_str = space.str_w(w_mode)

            if "+" in mode_str:
                mode = os.O_RDWR
                if "w" in mode_str:
                    mode |= os.O_CREAT | os.O_TRUNC
                elif "a" in mode_str:
                    mode |= os.O_CREAT | os.O_APPEND
            elif mode_str == "r":
                mode = os.O_RDONLY
            elif mode_str == "w":
                mode = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
            elif mode_str == "a":
                mode = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
            else:
                raise space.error(
                    space.getclassfor(W_ArgumentError), "invalid access mode %s" % mode_str
                )
        else:
            mode = space.int_w(w_mode)
        if w_perm_or_opt is not None or w_opt is not None:
            raise NotImplementedError("options hash or permissions for File.new")
        self.fd = os.open(filename, mode, perm)
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

    @classdef.singleton_method("join")
    def singleton_method_join(self, space, args_w):
        sep = space.str_w(space.find_const(self, "SEPARATOR"))
        result = []
        for w_arg in args_w:
            if isinstance(w_arg, W_ArrayObject):
                string = space.str_w(
                    W_FileObject.singleton_method_join(self, space, space.listview(w_arg))
                )
            else:
                string = space.str_w(w_arg)
            if string.startswith(sep):
                while result and result[-1] == sep:
                    result.pop()
            elif result and not result[-1] == sep:
                result += sep
            result += string
        return space.newstr_fromchars(result)

    @classdef.singleton_method("exists?", filename="str")
    @classdef.singleton_method("exist?", filename="str")
    def method_existp(self, space, filename):
        return space.newbool(os.path.exists(filename))

    @classdef.singleton_method("file?", filename="str")
    def method_filep(self, space, filename):
        return space.newbool(os.path.isfile(filename))

    @classdef.singleton_method("executable?", filename="str")
    def method_executablep(self, space, filename):
        return space.newbool(os.path.isfile(filename) and os.access(filename, os.X_OK))
