from __future__ import absolute_import

import os

from rpython.rlib import jit, rbigint, unroll, rgc, _rsocket_rffi
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform

from topaz.module import ModuleDef
from topaz.system import IS_WINDOWS


if not IS_WINDOWS:
    class CConstants(object):
        _compilation_info_ = ExternalCompilationInfo(includes=['fcntl.h'])
    for const in ["F_DUPFD", "F_GETFD", "F_GETLK", "F_SETFD", "F_GETFL",
                  "F_SETFL", "F_SETLK", "F_SETLKW", "FD_CLOEXEC", "F_RDLCK",
                  "F_UNLCK", "F_WRLCK", "O_CREAT", "O_EXCL", "O_NOCTTY",
                  "O_TRUNC", "O_APPEND", "O_NONBLOCK", "O_NDELAY", "O_RDONLY",
                  "O_RDWR", "O_WRONLY", "O_ACCMODE"]:
        setattr(CConstants, const, rffi_platform.ConstantInteger(const))
    fcntl_constants = rffi_platform.configure(CConstants)
    fcntl = _rsocket_rffi.fcntl
else:
    fcntl_constants = {}
    def fcntl(fdtype, cmd, arg):
        raise NotImplementedError


class Fcntl(object):
    moduledef = ModuleDef("Fcntl")

    @moduledef.setup_module
    def setup_module(space, w_mod):
        if not IS_WINDOWS:
            for key, value in fcntl_constants.items():
                space.set_const(w_mod, const, space.newint(value))
