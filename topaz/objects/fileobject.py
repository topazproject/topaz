import os
import sys

from topaz.coerce import Coerce
from topaz.module import ClassDef
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.hashobject import W_HashObject
from topaz.objects.objectobject import W_Object
from topaz.objects.stringobject import W_StringObject


FNM_NOESCAPE = 0x01
FNM_PATHNAME = 0x02
FNM_DOTMATCH = 0x04
if sys.platform == "win32":
    O_BINARY = os.O_BINARY
else:
    O_BINARY = 0


class W_IOObject(W_Object):
    classdef = ClassDef("IO", W_Object.classdef, filepath=__file__)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.fd = -1

    def __del__(self):
        # Do not close standard file streams
        if self.fd > 3:
            os.close(self.fd)

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
        self.ensure_not_closed(space)
        if w_length:
            length = space.int_w(w_length)
            if length < 0:
                raise space.error(space.w_ArgumentError,
                    "negative length %d given" % length
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

    classdef.app_method("""
    def << s
        write(s)
        return self
    end
    """)

    @classdef.method("write")
    def method_write(self, space, w_str):
        self.ensure_not_closed(space)
        string = space.str_w(space.send(w_str, space.newsymbol("to_s")))
        bytes_written = os.write(self.fd, string)
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
            sep = space.str_w(space.send(w_sep, space.newsymbol("to_s")))
        else:
            sep = ""
        w_end = space.globals.get(space, "$\\")
        if w_end:
            end = space.str_w(space.send(w_end, space.newsymbol("to_s")))
        else:
            end = ""
        strings = [space.str_w(space.send(w_arg, space.newsymbol("to_s"))) for w_arg in args_w]
        os.write(self.fd, sep.join(strings))
        os.write(self.fd, end)
        return space.w_nil

    @classdef.method("puts")
    def method_puts(self, space, args_w):
        self.ensure_not_closed(space)
        for w_arg in args_w:
            string = space.str_w(space.send(w_arg, space.newsymbol("to_s")))
            os.write(self.fd, string)
            if not string.endswith("\n"):
                os.write(self.fd, "\n")
        return space.w_nil

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

    classdef.app_method("""
    def self.popen(cmd, mode='r', opts={}, &block)
        r, w = IO.pipe
        if mode != 'r' && mode != 'w'
            raise NotImplementedError, "mode #{mode} for IO.popen"
        end

        pid = fork do
            if mode == 'r'
                r.close
                $stdout.reopen(w)
            else
                w.close
                $stdin.reopen(r)
            end
            exec *cmd
        end

        if mode == 'r'
            res = r
            w.close
        else
            res = w
            r.close
        end

        res.instance_variable_set("@pid", pid)
        block ? yield(res) : res
    end

    def pid
        @pid
    end
    """)

    @classdef.method("reopen")
    def method_reopen(self, space, w_io, w_mode=None):
        if not space.is_kind_of(w_io, space.getclassfor(W_IOObject)):
            args = [w_io] if w_mode is None else [w_io, w_mode]
            w_io = space.send(space.getclassfor(W_FileObject), space.newsymbol("new"), args)
        assert isinstance(w_io, W_IOObject)
        if self.fd >= 0:
            os.close(self.fd)
            os.dup2(w_io.getfd(), self.fd)
        else:
            self.fd = os.dup(w_io.getfd())
        return self

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

    classdef.app_method("""
    def each_line(sep=$/, limit=nil)
        if sep.is_a?(Fixnum) && limit.nil?
            limit = sep
            sep = $/
        end

        if sep.nil?
            yield(limit ? read(limit) : read)
            return self
        end

        rest = ""
        nxt = read(8192)
        need_read = false
        while nxt || rest
            if nxt and need_read
                rest = rest ? rest + nxt : nxt
                nxt = read(8192)
                need_read = false
            end

            line, rest = *rest.split(sep, 2)

            if limit && line.size > limit
                left = 0
                right = limit
                while right < line.size
                    yield line[left...right]
                    left, right = right, right + limit
                end
                rest = line[right - limit..-1] + sep + (rest || "")
            elsif rest || nxt.nil?
                yield line
            else
                need_read = true
            end
        end
        self
    end
    """)

    @classdef.method("close")
    def method_close(self, space):
        self.ensure_not_closed(space)
        os.close(self.fd)
        self.fd = -1
        return self

    @classdef.method("closed?")
    def method_closedp(self, space):
        return space.newbool(self.fd == -1)


class W_FileObject(W_IOObject):
    classdef = ClassDef("File", W_IOObject.classdef, filepath=__file__)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        if sys.platform == "win32":
            w_alt_seperator = space.newstr_fromstr("\\")
            w_fnm_syscase = space.newint(0x08)
        else:
            w_alt_seperator = space.w_nil
            w_fnm_syscase = space.newint(0)
        space.set_const(w_cls, "SEPARATOR", space.newstr_fromstr("/"))
        space.set_const(w_cls, "ALT_SEPARATOR", w_alt_seperator)
        space.set_const(w_cls, "FNM_SYSCASE", w_fnm_syscase)
        space.set_const(w_cls, "FNM_NOESCAPE", space.newint(FNM_NOESCAPE))
        space.set_const(w_cls, "FNM_PATHNAME", space.newint(FNM_PATHNAME))
        space.set_const(w_cls, "FNM_DOTMATCH", space.newint(FNM_DOTMATCH))
        space.set_const(w_cls, "BINARY", space.newint(O_BINARY))
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
        if w_mode is None:
            w_mode = space.w_nil
        if w_perm_or_opt is None:
            w_perm_or_opt = space.w_nil
        if w_opt is None:
            w_opt = space.w_nil
        if isinstance(w_perm_or_opt, W_HashObject):
            assert w_opt is space.w_nil
            perm = 0665
            w_opt = w_perm_or_opt
        elif w_opt is not space.w_nil:
            perm = space.int_w(w_perm_or_opt)
        else:
            perm = 0665
        if w_mode is space.w_nil:
            mode = os.O_RDONLY
        elif isinstance(w_mode, W_StringObject):
            mode_str = space.str_w(w_mode)
            mode = 0
            invalid_error = space.error(space.w_ArgumentError,
                "invalid access mode %s" % mode_str
            )
            major_mode_seen = False

            for ch in mode_str:
                if ch == "b":
                    mode |= O_BINARY
                elif ch == "+":
                    mode |= os.O_RDWR
                elif ch == "r":
                    if major_mode_seen:
                        raise invalid_error
                    major_mode_seen = True
                    mode |= os.O_RDONLY
                elif ch in "aw":
                    if major_mode_seen:
                        raise invalid_error
                    major_mode_seen = True
                    mode |= os.O_WRONLY | os.O_CREAT
                    if ch == "w":
                        mode |= os.O_TRUNC
                    else:
                        mode |= os.O_APPEND
                else:
                    raise invalid_error
        else:
            mode = space.int_w(w_mode)
        if w_perm_or_opt is not space.w_nil or w_opt is not space.w_nil:
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

    @classdef.singleton_method("expand_path", path="path")
    def method_expand_path(self, space, path, w_dir=None):
        if path and path[0] == "~":
            if len(path) >= 2 and path[1] == "/":
                path = os.environ["HOME"] + path[1:]
            elif len(path) < 2:
                return space.newstr_fromstr(os.environ["HOME"])
            else:
                raise NotImplementedError
        elif not path or path[0] != "/":
            if w_dir is not None and w_dir is not space.w_nil:
                dir = space.str_w(space.send(self, space.newsymbol("expand_path"), [w_dir]))
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

    @classdef.singleton_method("exists?", filename="path")
    @classdef.singleton_method("exist?", filename="path")
    def method_existp(self, space, filename):
        return space.newbool(os.path.exists(filename))

    @classdef.singleton_method("file?", filename="path")
    def method_filep(self, space, filename):
        return space.newbool(os.path.isfile(filename))

    @classdef.singleton_method("directory?", filename="path")
    def method_directoryp(self, space, filename):
        return space.newbool(os.path.isdir(filename))

    @classdef.singleton_method("executable?", filename="path")
    def method_executablep(self, space, filename):
        return space.newbool(os.path.isfile(filename) and os.access(filename, os.X_OK))

    @classdef.singleton_method("basename", filename="path")
    def method_basename(self, space, filename):
        i = filename.rfind('/') + 1
        assert i >= 0
        return space.newstr_fromstr(filename[i:])

    classdef.app_method("""
    def self.open(filename, mode="r", perm=nil, opt=nil, &block)
        f = self.new filename, mode, perm, opt
        return f unless block
        begin
            return yield f
        ensure
            f.close
        end
    end
    """)

    @classdef.method("truncate", length="int")
    def method_truncate(self, space, length):
        self.ensure_not_closed(space)
        os.ftruncate(self.fd, length)
        return space.newint(0)
