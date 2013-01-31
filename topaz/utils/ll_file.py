import os
import stat
import sys

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.tool import rffi_platform as platform
from rpython.translator.tool.cbuild import ExternalCompilationInfo


if sys.platform.startswith("win"):
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

    def isdir(path):
        try:
            st = os.stat(path)
        except os.error:
            return False
        return stat.S_ISDIR(st.st_mode)
else:
    O_BINARY = 0
    def ftruncate(fd, size):
        os.ftruncate(fd, size)

    def isdir(path):
        return os.path.isdir(path)
