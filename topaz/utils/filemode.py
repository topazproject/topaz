import os

from topaz.objects.stringobject import W_StringObject
from topaz.utils.ll_file import O_BINARY


def map_filemode(space, w_mode):
    encoding = ""
    if w_mode is space.w_nil:
        mode = os.O_RDONLY
    elif isinstance(w_mode, W_StringObject):
        mode_str = space.str_w(w_mode)
        mode = 0
        invalid_error = space.error(space.w_ArgumentError,
            "invalid access mode %s" % mode_str
        )
        major_mode_seen = False
        readable = writeable = append = False

        pos = 0
        for ch in mode_str:
            pos += 1
            if ch == "b":
                mode |= O_BINARY
            elif ch == "+":
                readable = writeable = True
            elif ch == "r":
                if major_mode_seen:
                    raise invalid_error
                major_mode_seen = True
                readable = True
            elif ch == "a":
                if major_mode_seen:
                    raise invalid_error
                major_mode_seen = True
                mode |= os.O_CREAT
                append = writeable = True
            elif ch == "w":
                if major_mode_seen:
                    raise invalid_error
                major_mode_seen = True
                mode |= os.O_TRUNC | os.O_CREAT
                writeable = True
            elif ch == ":":
                encoding = mode_str[pos + 1:]
                break
            else:
                raise invalid_error
        if readable and writeable:
            mode |= os.O_RDWR
        elif readable:
            mode |= os.O_RDONLY
        elif writeable:
            mode |= os.O_WRONLY
        if append:
            mode |= os.O_APPEND
    else:
        mode = space.int_w(w_mode)
    return (mode, encoding)
