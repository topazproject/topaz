import sys

from pypy.rpython.lltypesystem import rffi
from pypy.rpython.lltypesystem import lltype
from pypy.rpython.tool import rffi_platform as platform
from pypy.rlib import rposix
from pypy.translator.tool.cbuild import ExternalCompilationInfo


if sys.platform.startswith('win'):
    def opendir(_):
        raise NotImplementedError("directory operations on windows")
    readdir = closedir = opendir
else:
    compilation_info = ExternalCompilationInfo(
        includes = ['sys/types.h', 'dirent.h']
    )
    class CConfig:
        _compilation_info_ = compilation_info
        DIRENT = platform.Struct('struct dirent',
                                 [('d_name', lltype.FixedSizeArray(rffi.CHAR, 1))])
    DIRP = rffi.COpaquePtr('DIR')
    config = platform.configure(CConfig)
    DIRENT = config['DIRENT']
    DIRENTP = lltype.Ptr(DIRENT)

    # XXX macro=True is hack to make sure we get the correct kind of
    # dirent struct (which depends on defines)
    os_opendir = rffi.llexternal('opendir', [rffi.CCHARP], DIRP,
                                 compilation_info=compilation_info,
                                 macro=True)
    os_readdir = rffi.llexternal('readdir', [DIRP], DIRENTP,
                                 compilation_info=compilation_info,
                                 macro=True)
    os_closedir = rffi.llexternal('closedir', [DIRP], rffi.INT,
                                  compilation_info=compilation_info,
                                  macro=True)

    def opendir(path):
        dirp = os_opendir(path)
        if not dirp:
            return (None, rposix.get_errno())
        else:
            rposix.set_errno(0)
            return (dirp, 0)

    def closedir(dirp):
        os_closedir(dirp)

    def readdir(dirp):
        direntp = os_readdir(dirp)
        if not direntp:
            return (None, rposix.get_errno())
        else:
            namep = rffi.cast(rffi.CCHARP, direntp.c_d_name)
            name = rffi.charp2str(namep)
            return (name, 0)
