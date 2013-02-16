import os
import stat
import sys

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.tool import rffi_platform as platform
from rpython.translator.tool.cbuild import ExternalCompilationInfo

from topaz.system import WINDOWS

if WINDOWS:
    O_BINARY = os.O_BINARY

    eci = ExternalCompilationInfo(includes=['windows.h'])
    class CConfig:
        _compilation_info_ = eci
    config = platform.configure(CConfig)

    _chsize = rffi.llexternal('_chsize',
        [rffi.INT, rffi.LONG], rffi.INT,
        compilation_info=eci,
    )

    def ftruncate(fd, size):
        _chsize(fd, size)

    # This imports the definition of isdir that uses stat. On Windows
    # this is replaced in the path module with a version that isn't
    # RPython
    from genericpath import isdir
else:
    O_BINARY = 0
    ftruncate = os.ftruncate
    isdir = os.path.isdir
