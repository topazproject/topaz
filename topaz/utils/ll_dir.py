from rpython.rlib import rposix
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rtyper.tool import rffi_platform as platform
from rpython.translator.tool.cbuild import ExternalCompilationInfo

from topaz.system import IS_WINDOWS


if IS_WINDOWS:
    def opendir(_):
        raise NotImplementedError("directory operations on windows")
    readdir = closedir = opendir
else:
    eci = ExternalCompilationInfo(
        includes=["sys/types.h", "dirent.h"]
    )

    class CConfig:
        _compilation_info_ = eci
        DIRENT = platform.Struct("struct dirent", [
            ("d_name", lltype.FixedSizeArray(rffi.CHAR, 1))
        ])
    config = platform.configure(CConfig)
    DIRP = rffi.COpaquePtr("DIR")
    DIRENT = config["DIRENT"]
    DIRENTP = lltype.Ptr(DIRENT)

    # XXX macro=True is hack to make sure we get the correct kind of
    # dirent struct (which depends on defines)
    os_opendir = rffi.llexternal("opendir",
        [rffi.CCHARP], DIRP,
        compilation_info=eci,
        save_err=rffi.RFFI_SAVE_ERRNO,
        macro=True
    )
    os_readdir = rffi.llexternal("readdir",
        [DIRP], DIRENTP,
        compilation_info=eci,
        save_err=rffi.RFFI_SAVE_ERRNO,
        macro=True
    )
    os_closedir = rffi.llexternal("closedir",
        [DIRP], rffi.INT,
        compilation_info=eci,
        releasegil=False,
        macro=True
    )

    def opendir(path):
        dirp = os_opendir(path)
        if not dirp:
            raise OSError(rposix.get_saved_errno(), "error in opendir")
        return dirp

    def closedir(dirp):
        os_closedir(dirp)

    def readdir(dirp):
        rposix.set_saved_errno(0)
        direntp = os_readdir(dirp)
        if not direntp:
            if rposix.get_saved_errno() == 0:
                return None
            else:
                raise OSError(rposix.get_saved_errno(), "error in readdir")
        namep = rffi.cast(rffi.CCHARP, direntp.c_d_name)
        return rffi.charp2str(namep)
