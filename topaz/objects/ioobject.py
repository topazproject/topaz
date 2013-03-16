import os

from rpython.rlib.streamio import DiskFile, construct_stream_tower

from topaz.coerce import Coerce
from topaz.error import error_for_oserror
from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.objects.stringobject import W_StringObject
from topaz.utils.filemode import map_filemode, decode_filemode


def construct_diskio_stream_tower(fd, mode, textmode=False, binmode=False,
                                 buffering=True):
    # The "textmode", "binmode", and "buffering" flags won't be used at least
    # until the IO.new options hash support is implemented.
    os_flags, reading, writing, basemode, binary, text = decode_filemode(mode)
    return construct_stream_tower(
        DiskFile(fd),
        1 if buffering else 0,
        True, # XXX "universal" (applicability??)
        reading,
        writing,
        binary or binmode or not text or not textmode # FIXME please. egad.
    )


class W_IOObject(W_Object):
    classdef = ClassDef("IO", W_Object.classdef, filepath=__file__)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.fd = -1
        self.mode = None
        self.stream = None
        self.sync = True # XXX or False?  need to look at MRI more...

    def __del__(self):
        # Do not close standard file streams
        if self.fd > 3:
            self.stream.close()

    def __deepcopy__(self, memo):
        obj = super(W_IOObject, self).__deepcopy__(memo)
        obj.fd = self.fd
        obj.mode = self.mode
        # XXX is the following remotely correct?  if the stream is buffered,
        # we'd be losing the buffer position, for example...
        obj.stream = construct_diskio_stream_tower(self.fd, self.mode)
        obj.sync = self.sync
        return obj

    def ensure_not_closed(self, space):
        if self.fd < 0:
            raise space.error(space.w_IOError, "closed stream")

        # XXX HALP XXX This is almost certanly a horrible thing to do, and the
        # wrong place to do it.  Why are the instance attributes sometimes set
        # as though `method_initialize` has been called yet other times only as
        # though `__init__` has been called?
        if self.stream is None:
            self.stream = construct_diskio_stream_tower(
                self.fd,
                self.mode if self.mode is not None else "r"
            )

    def getfd(self):
        return self.fd

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        w_stdin = space.send(w_cls, space.newsymbol("new"), [space.newint(0)])
        space.globals.set(space, "$stdin", w_stdin)
        space.set_const(space.w_object, "STDIN", w_stdin)

        w_stdout = space.send(w_cls, space.newsymbol("new"), [space.newint(1)])
        space.globals.set(space, "$stdout", w_stdout)
        space.globals.set(space, "$>", w_stdout)
        space.globals.set(space, "$/", space.newstr_fromstr("\n"))
        space.set_const(space.w_object, "STDOUT", w_stdout)

        w_stderr = space.send(w_cls, space.newsymbol("new"), [space.newint(2)])
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
            mode = map_filemode(space, w_mode_str_or_int)
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
            if ":" in mode:
                raise space.error(space.w_NotImplementedError, "encoding for IO.new")
        elif w_mode_str_or_int is None:
            mode = None
        else:
            raise space.error(space.w_NotImplementedError, "int mode for IO.new")
        if w_opts is not None:
            raise space.error(space.w_NotImplementedError, "options hash for IO.new")
        if mode is None:
            mode = "r"
        self.mode = mode
        self.fd = fd
        self.stream = construct_diskio_stream_tower(fd, mode)
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
        else:
            length = -1
        read_str = self.stream.read(length)
        if not read_str:
            return space.w_nil
        w_read_str = space.newstr_fromstr(read_str)
        if w_str is not None:
            w_str.clear(space)
            w_str.extend(space, w_read_str)
            return w_str
        else:
            return w_read_str

    @classdef.method("write")
    def method_write(self, space, w_str):
        self.ensure_not_closed(space)
        string = space.str_w(space.send(w_str, space.newsymbol("to_s")))
        self.stream.write(string)
        if self.sync and self.stream.flushable():
            self.stream.flush()
        # the rpython streamio API seems to guarantee this is fully written (??)
        return space.newint(len(string))

    @classdef.method("flush")
    def method_flush(self, space):
        # We have no internal buffers to flush!
        self.ensure_not_closed(space)
        if self.stream.flushable():
            self.stream.flush()
        return self

    @classdef.method("seek", amount="int", whence="int")
    def method_seek(self, space, amount, whence=os.SEEK_SET):
        self.ensure_not_closed(space)
        self.stream.seek(amount, whence)
        return space.newint(0)

    @classdef.method("pos")
    @classdef.method("tell")
    def method_pos(self, space):
        self.ensure_not_closed(space)
        # TODO: this currently truncates large values, switch this to use a
        # Bignum in those cases
        return space.newint(int(self.stream.tell()))

    @classdef.method("rewind")
    def method_rewind(self, space):
        self.ensure_not_closed(space)
        self.stream.seek(0, os.SEEK_SET)
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
            sep = space.str_w(space.send(w_sep, space.newsymbol("to_s")))
        else:
            sep = ""
        w_end = space.globals.get(space, "$\\")
        if w_end:
            end = space.str_w(space.send(w_end, space.newsymbol("to_s")))
        else:
            end = ""
        strings = [space.str_w(space.send(w_arg, space.newsymbol("to_s"))) for w_arg in args_w]
        self.stream.write(sep.join(strings))
        self.stream.write(end)
        if self.sync and self.stream.flushable():
            self.stream.flush()
        return space.w_nil

    @classdef.method("getc")
    def method_getc(self, space):
        self.ensure_not_closed(space)
        c = self.stream.read(1)
        if not c:
            return space.w_nil
        return space.newstr_fromstr(c)

    @classdef.singleton_method("pipe")
    def method_pipe(self, space, block=None):
        r, w = os.pipe()
        pipes_w = [
            space.send(self, space.newsymbol("new"), [space.newint(r)]),
            space.send(self, space.newsymbol("new"), [space.newint(w)])
        ]
        if block is not None:
            try:
                return space.invoke_block(block, pipes_w)
            finally:
                for pipe_w in pipes_w:
                    if not space.is_true(space.send(pipe_w, space.newsymbol("closed?"))):
                        space.send(pipe_w, space.newsymbol("close"))
        else:
            return space.newarray(pipes_w)

    @classdef.method("reopen")
    def method_reopen(self, space, w_arg, w_mode=None):
        self.ensure_not_closed(space)
        w_io = space.convert_type(w_arg, space.w_io, "to_io", raise_error=False)
        if w_io is space.w_nil:
            from topaz.objects.fileobject import W_FileObject
            args = [w_arg] if w_mode is None else [w_arg, w_mode]
            w_io = space.send(space.getclassfor(W_FileObject), space.newsymbol("new"), args)
        assert isinstance(w_io, W_IOObject)
        w_io.ensure_not_closed(space)
        self.stream.close()
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
        self.stream.close()
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
