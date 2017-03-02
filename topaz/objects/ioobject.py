import os

from rpython.rlib.rpoll import POLLIN, PollError

from topaz.coerce import Coerce
from topaz.error import error_for_oserror
from topaz.module import ClassDef
from topaz.modules.fcntl import fcntl
from topaz.objects.objectobject import W_Object
from topaz.objects.stringobject import W_StringObject
from topaz.utils.filemode import map_filemode
from topaz.utils.ll_file import close_without_validation
from topaz.system import IS_WINDOWS


if IS_WINDOWS:
    from rpython.rlib.rpoll import _poll as poll
else:
    from rpython.rlib.rpoll import poll


class W_IOObject(W_Object):
    classdef = ClassDef("IO", W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.fd = -1

    def __del__(self):
        # Do not close standard file streams
        if self.fd > 3:
            close_without_validation(self.fd)

    def __deepcopy__(self, memo):
        obj = super(W_IOObject, self).__deepcopy__(memo)
        obj.fd = self.fd
        return obj

    def ensure_not_closed(self, space):
        if self.fd < 0:
            raise space.error(space.w_IOError, "closed stream")

    def getfd(self):
        return self.fd

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        w_stdin = space.send(w_cls, "new", [space.newint(0)])
        space.globals.set(space, "$stdin", w_stdin)
        space.set_const(space.w_object, "STDIN", w_stdin)

        w_stdout = space.send(w_cls, "new", [space.newint(1)])
        space.globals.set(space, "$stdout", w_stdout)
        space.globals.set(space, "$>", w_stdout)
        space.globals.set(space, "$/", space.newstr_fromstr("\n"))
        space.set_const(space.w_object, "STDOUT", w_stdout)

        w_stderr = space.send(w_cls, "new", [space.newint(2)])
        space.globals.set(space, "$stderr", w_stderr)
        space.set_const(space.w_object, "STDERR", w_stderr)

        space.set_const(w_cls, "SEEK_CUR", space.newint(os.SEEK_CUR))
        space.set_const(w_cls, "SEEK_END", space.newint(os.SEEK_END))
        space.set_const(w_cls, "SEEK_SET", space.newint(os.SEEK_SET))

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_IOObject(space)

    @classdef.singleton_method("sysopen")
    def method_sysopen(self, space, w_path, w_mode_str_or_int=None, w_perm=None):
        perm = 0666
        mode = os.O_RDONLY
        if w_mode_str_or_int is not None:
            mode, encoding = map_filemode(space, w_mode_str_or_int)
        if w_perm is not None and w_perm is not space.w_nil:
            perm = space.int_w(w_perm)
        path = Coerce.path(space, w_path)
        try:
            fd = os.open(path, mode, perm)
        except OSError as e:
            raise error_for_oserror(space, e)
        else:
            return space.newint(fd)

    @classdef.method("initialize")
    def method_initialize(self, space, w_fd_or_io, w_mode_str_or_int=None, w_opts=None):
        if isinstance(w_fd_or_io, W_IOObject):
            fd = w_fd_or_io.fd
        else:
            fd = Coerce.int(space, w_fd_or_io)
        if isinstance(w_mode_str_or_int, W_StringObject):
            mode = space.str_w(w_mode_str_or_int)
        elif w_mode_str_or_int is None:
            mode = None
        else:
            raise space.error(space.w_NotImplementedError, "int mode for IO.new")
        if w_opts is not None:
            raise space.error(space.w_NotImplementedError, "options hash for IO.new")
        if mode is None:
            mode = "r"
        self.fd = fd
        return self

    @classdef.method("read")
    def method_read(self, space, w_length=None, w_str=None):
        self.ensure_not_closed(space)
        if w_length:
            length = space.int_w(w_length)
            if length < 0:
                raise space.error(space.w_ArgumentError,
                    "negative length %d given" % length
                )
            elif length == 0:
                return space.newstr_fromstr("")
        else:
            length = -1
        read_bytes = 0
        read_chunks = []
        while length < 0 or read_bytes < length:
            if length > 0:
                max_read = int(length - read_bytes)
            else:
                max_read = 8192
            try:
                current_read = os.read(self.fd, max_read)
            except OSError as e:
                raise error_for_oserror(space, e)
            if len(current_read) == 0:
                break
            read_bytes += len(current_read)
            read_chunks += current_read
        # Return nil on EOF if length is given
        if read_bytes == 0 and length > 0:
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
        self.ensure_not_closed(space)
        string = space.str_w(space.send(w_str, "to_s"))
        try:
            bytes_written = os.write(self.fd, string)
        except OSError as e:
            raise error_for_oserror(space, e)
        return space.newint(bytes_written)

    @classdef.method("flush")
    def method_flush(self, space):
        # We have no internal buffers to flush!
        self.ensure_not_closed(space)
        return self

    @classdef.method("seek", amount="int", whence="int")
    def method_seek(self, space, amount, whence=os.SEEK_SET):
        self.ensure_not_closed(space)
        os.lseek(self.fd, amount, whence)
        return space.newint(0)

    @classdef.method("pos")
    @classdef.method("tell")
    def method_pos(self, space):
        self.ensure_not_closed(space)
        # TODO: this currently truncates large values, switch this to use a
        # Bignum in those cases
        return space.newint(int(os.lseek(self.fd, 0, os.SEEK_CUR)))

    @classdef.method("rewind")
    def method_rewind(self, space):
        self.ensure_not_closed(space)
        os.lseek(self.fd, 0, os.SEEK_SET)
        return space.newint(0)

    @classdef.method("print")
    def method_print(self, space, args_w):
        self.ensure_not_closed(space)
        if not args_w:
            w_last = space.globals.get(space, "$_")
            if w_last is not None:
                args_w.append(w_last)
        w_sep = space.globals.get(space, "$,")
        if w_sep:
            sep = space.str_w(space.send(w_sep, "to_s"))
        else:
            sep = ""
        w_end = space.globals.get(space, "$\\")
        if w_end:
            end = space.str_w(space.send(w_end, "to_s"))
        else:
            end = ""
        strings = [space.str_w(space.send(w_arg, "to_s")) for w_arg in args_w]
        os.write(self.fd, sep.join(strings))
        os.write(self.fd, end)
        return space.w_nil

    @classdef.method("getc")
    def method_getc(self, space):
        self.ensure_not_closed(space)
        try:
            c = os.read(self.fd, 1)
        except OSError as e:
            raise error_for_oserror(space, e)
        if not c:
            return space.w_nil
        return space.newstr_fromstr(c)

    @classdef.singleton_method("pipe")
    def method_pipe(self, space, block=None):
        r, w = os.pipe()
        pipes_w = [
            space.send(self, "new", [space.newint(r)]),
            space.send(self, "new", [space.newint(w)])
        ]
        if block is not None:
            try:
                return space.invoke_block(block, pipes_w)
            finally:
                for pipe_w in pipes_w:
                    if not space.is_true(space.send(pipe_w, "closed?")):
                        space.send(pipe_w, "close")
        else:
            return space.newarray(pipes_w)

    @classdef.method("reopen")
    def method_reopen(self, space, w_arg, w_mode=None):
        self.ensure_not_closed(space)
        w_io = space.convert_type(w_arg, space.w_io, "to_io", raise_error=False)
        if w_io is space.w_nil:
            from topaz.objects.fileobject import W_FileObject
            args = [w_arg] if w_mode is None else [w_arg, w_mode]
            w_io = space.send(space.getclassfor(W_FileObject), "new", args)
        assert isinstance(w_io, W_IOObject)
        w_io.ensure_not_closed(space)
        os.close(self.fd)
        os.dup2(w_io.getfd(), self.fd)
        return self

    @classdef.method("to_io")
    def method_to_io(self):
        return self

    @classdef.method("fileno")
    @classdef.method("to_i")
    def method_to_i(self, space):
        self.ensure_not_closed(space)
        return space.newint(self.fd)

    @classdef.method("close")
    def method_close(self, space):
        self.ensure_not_closed(space)
        os.close(self.fd)
        self.fd = -1
        return self

    @classdef.method("closed?")
    def method_closedp(self, space):
        return space.newbool(self.fd == -1)

    @classdef.method("stat")
    def method_stat(self, space):
        from topaz.objects.fileobject import W_FileStatObject
        try:
            stat_val = os.fstat(self.fd)
        except OSError as e:
            raise error_for_oserror(space, e)
        stat_obj = W_FileStatObject(space)
        stat_obj.set_stat(stat_val)
        return stat_obj

    @classdef.method("isatty")
    @classdef.method("tty?")
    def method_isatty(self, space):
        self.ensure_not_closed(space)
        return space.newbool(os.isatty(self.fd))

    @classdef.method("fcntl", cmd="int", arg="int")
    def method_fcntl(self, space, cmd, arg=0):
        fcntl(self.fd, cmd, arg)
        return self

    @classdef.method("ready?")
    def method_ready(self, space):
        retval = None
        try:
            retval = poll({self.fd: POLLIN}, 0)
        except PollError:
            return space.w_nil
        return space.newbool(len(retval) > 0)
