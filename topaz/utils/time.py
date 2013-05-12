# Time utilities extracted from `pypy.module.rctime.interp_time`
# TODO put most of this into `rpython.rlib.rtime`
from __future__ import absolute_import

import os
import sys
import time as pytime

from topaz import system

from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype
from rpython.rlib.rarithmetic import ovfcheck_float_to_int, intmask
from rpython.rlib import rposix
from rpython.translator.tool.cbuild import ExternalCompilationInfo

_time_zones = []
if system.IS_CYGWIN:
    _time_zones = ["GMT-12", "GMT-11", "GMT-10", "GMT-9", "GMT-8", "GMT-7",
                   "GMT-6", "GMT-5", "GMT-4", "GMT-3", "GMT-2", "GMT-1",
                   "GMT",  "GMT+1", "GMT+2", "GMT+3", "GMT+4", "GMT+5",
                   "GMT+6",  "GMT+7", "GMT+8", "GMT+9", "GMT+10", "GMT+11",
                   "GMT+12",  "GMT+13", "GMT+14"]

## if system.IS_WINDOWS:
##     # Interruptible sleeps on Windows:
##     # We install a specific Console Ctrl Handler which sets an 'event'.
##     # time.sleep() will actually call WaitForSingleObject with the desired
##     # timeout.  On Ctrl-C, the signal handler is called, the event is set,
##     # and the wait function exits.
##     from rpython.rlib import rwin32
##     from pypy.interpreter.error import wrap_windowserror, wrap_oserror
##     from rpython.rlib import rthread as thread

##     eci = ExternalCompilationInfo(
##         includes = ['windows.h'],
##         post_include_bits = ["BOOL pypy_timemodule_setCtrlHandler(HANDLE event);"],
##         separate_module_sources=['''
##             static HANDLE interrupt_event;

##             static BOOL WINAPI CtrlHandlerRoutine(
##               DWORD dwCtrlType)
##             {
##                 SetEvent(interrupt_event);
##                 /* allow other default handlers to be called.
##                  * Default Python handler will setup the
##                  * KeyboardInterrupt exception.
##                  */
##                 return 0;
##             }

##             BOOL pypy_timemodule_setCtrlHandler(HANDLE event)
##             {
##                 interrupt_event = event;
##                 return SetConsoleCtrlHandler(CtrlHandlerRoutine, TRUE);
##             }

##         '''],
##         export_symbols=['pypy_timemodule_setCtrlHandler'],
##         )
##     _setCtrlHandlerRoutine = rffi.llexternal(
##         'pypy_timemodule_setCtrlHandler',
##         [rwin32.HANDLE], rwin32.BOOL,
##         compilation_info=eci)

##     class GlobalState:
##         def __init__(self):
##             self.init()

##         def init(self):
##             self.interrupt_event = rwin32.NULL_HANDLE

##         def startup(self, space):
##             # Initialize the event handle used to signal Ctrl-C
##             try:
##                 globalState.interrupt_event = rwin32.CreateEvent(
##                     rffi.NULL, True, False, rffi.NULL)
##             except WindowsError, e:
##                 raise wrap_windowserror(space, e)
##             if not _setCtrlHandlerRoutine(globalState.interrupt_event):
##                 raise wrap_windowserror(
##                     space, rwin32.lastWindowsError("SetConsoleCtrlHandler"))

##     globalState = GlobalState()

##     class State:
##         def __init__(self, space):
##             self.main_thread = 0

##         def _cleanup_(self):
##             self.main_thread = 0
##             globalState.init()

##         def startup(self, space):
##             self.main_thread = thread.get_ident()
##             globalState.startup(space)

##         def get_interrupt_event(self):
##             return globalState.interrupt_event


_includes = ["time.h"]
if system.IS_POSIX:
    _includes.append('sys/time.h')

class CConfig:
    _compilation_info_ = ExternalCompilationInfo(
        includes = _includes
    )
    CLOCKS_PER_SEC = platform.ConstantInteger("CLOCKS_PER_SEC")
    clock_t = platform.SimpleType("clock_t", rffi.ULONG)
    has_gettimeofday = platform.Has('gettimeofday')

if system.IS_POSIX:
    calling_conv = 'c'
    CConfig.timeval = platform.Struct("struct timeval",
                                      [("tv_sec", rffi.INT),
                                       ("tv_usec", rffi.INT)])
    if system.IS_CYGWIN:
        CConfig.tm = platform.Struct("struct tm", [("tm_sec", rffi.INT),
            ("tm_min", rffi.INT), ("tm_hour", rffi.INT), ("tm_mday", rffi.INT),
            ("tm_mon", rffi.INT), ("tm_year", rffi.INT), ("tm_wday", rffi.INT),
            ("tm_yday", rffi.INT), ("tm_isdst", rffi.INT)])
    else:
        CConfig.tm = platform.Struct("struct tm", [("tm_sec", rffi.INT),
            ("tm_min", rffi.INT), ("tm_hour", rffi.INT), ("tm_mday", rffi.INT),
            ("tm_mon", rffi.INT), ("tm_year", rffi.INT), ("tm_wday", rffi.INT),
            ("tm_yday", rffi.INT), ("tm_isdst", rffi.INT), ("tm_gmtoff", rffi.LONG),
            ("tm_zone", rffi.CCHARP)])
## elif system.IS_WINDOWS:
##     calling_conv = 'win'
##     CConfig.tm = platform.Struct("struct tm", [("tm_sec", rffi.INT),
##         ("tm_min", rffi.INT), ("tm_hour", rffi.INT), ("tm_mday", rffi.INT),
##         ("tm_mon", rffi.INT), ("tm_year", rffi.INT), ("tm_wday", rffi.INT),
##         ("tm_yday", rffi.INT), ("tm_isdst", rffi.INT)])

class cConfig:
    pass

for k, v in platform.configure(CConfig).items():
    setattr(cConfig, k, v)
cConfig.tm.__name__ = "_tm"

def external(name, args, result, eci=CConfig._compilation_info_):
##     if system.IS_WINDOWS and rffi.sizeof(rffi.TIME_T) == 8:
##         # Recent Microsoft compilers use 64bit time_t and
##         # the corresponding functions are named differently
##         if (rffi.TIME_T in args or rffi.TIME_TP in args
##             or result in (rffi.TIME_T, rffi.TIME_TP)):
##             name = '_' + name + '64'
    return rffi.llexternal(name, args, result,
                           compilation_info=eci,
                           calling_conv=calling_conv,
                           threadsafe=False)

if system.IS_POSIX:
    cConfig.timeval.__name__ = "_timeval"
    timeval = cConfig.timeval

CLOCKS_PER_SEC = cConfig.CLOCKS_PER_SEC
clock_t = cConfig.clock_t
tm = cConfig.tm
glob_buf = lltype.malloc(tm, flavor='raw', zero=True, immortal=True)

if cConfig.has_gettimeofday:
    c_gettimeofday = external('gettimeofday', [rffi.VOIDP, rffi.VOIDP], rffi.INT)
TM_P = lltype.Ptr(tm)
c_clock = external('clock', [rffi.TIME_TP], clock_t)
c_time = external('time', [rffi.TIME_TP], rffi.TIME_T)
c_ctime = external('ctime', [rffi.TIME_TP], rffi.CCHARP)
c_gmtime = external('gmtime', [rffi.TIME_TP], TM_P)
c_mktime = external('mktime', [TM_P], rffi.TIME_T)
c_asctime = external('asctime', [TM_P], rffi.CCHARP)
c_localtime = external('localtime', [rffi.TIME_TP], TM_P)
if system.IS_POSIX:
    c_tzset = external('tzset', [], lltype.Void)
## if system.IS_WINDOWS:
##     win_eci = ExternalCompilationInfo(
##         includes = ["time.h"],
##         post_include_bits = ["long pypy_get_timezone();",
##                              "int pypy_get_daylight();",
##                              "char** pypy_get_tzname();"],
##         separate_module_sources = ["""
##         long pypy_get_timezone() { return timezone; }
##         int pypy_get_daylight() { return daylight; }
##         char** pypy_get_tzname() { return tzname; }
##         """],
##         export_symbols = [
##         '_tzset', 'pypy_get_timezone', 'pypy_get_daylight', 'pypy_get_tzname'],
##         )
##     # Ensure sure that we use _tzset() and timezone from the same C Runtime.
##     c_tzset = external('_tzset', [], lltype.Void, win_eci)
##     c_get_timezone = external('pypy_get_timezone', [], rffi.LONG, win_eci)
##     c_get_daylight = external('pypy_get_daylight', [], rffi.INT, win_eci)
##     c_get_tzname = external('pypy_get_tzname', [], rffi.CCHARPP, win_eci)

c_strftime = external('strftime', [rffi.CCHARP, rffi.SIZE_T, rffi.CCHARP, TM_P],
                      rffi.SIZE_T)

def _init_accept2dyear(space):
    if os.environ.get("PYTHONY2K"):
        accept2dyear = 0
    else:
        accept2dyear = 1
    _set_time_attr(space, "ACCEPT2DYEAR", space.newint(accept2dyear))

def _init_timezone(space):
    timezone = daylight = altzone = 0
    tzname = ["", ""]

##     if system.IS_WINDOWS:
##          c_tzset()
##          timezone = c_get_timezone()
##          altzone = timezone - 3600
##          daylight = c_get_daylight()
##          tzname_ptr = c_get_tzname()
##          tzname = rffi.charp2str(tzname_ptr[0]), rffi.charp2str(tzname_ptr[1])

    if system.IS_POSIX:
        if system.IS_CYGWIN:
            YEAR = (365 * 24 + 6) * 3600

            # about January 11th
            t = (((c_time(lltype.nullptr(rffi.TIME_TP.TO))) / YEAR) * YEAR + 10 * 24 * 3600)
            # we cannot have reference to stack variable, put it on the heap
            t_ref = lltype.malloc(rffi.TIME_TP.TO, 1, flavor='raw')
            t_ref[0] = rffi.cast(rffi.TIME_T, t)
            p = c_localtime(t_ref)
            q = c_gmtime(t_ref)
            janzone = (p.c_tm_hour + 24 * p.c_tm_mday) - (q.c_tm_hour + 24 * q.c_tm_mday)
            if janzone < -12:
                janname = "   "
            elif janzone > 14:
                janname = "   "
            else:
                janname = _time_zones[janzone - 12]
            janzone = janzone * 3600
            # about July 11th
            tt = t + YEAR / 2
            t_ref[0] = rffi.cast(rffi.TIME_T, tt)
            p = c_localtime(t_ref)
            q = c_gmtime(t_ref)
            julyzone = (p.c_tm_hour + 24 * p.c_tm_mday) - (q.c_tm_hour + 24 * q.c_tm_mday)
            if julyzone < -12:
                julyname = "   "
            elif julyzone > 14:
                julyname = "   "
            else:
                julyname = _time_zones[julyzone - 12]
            julyzone = julyzone * 3600
            lltype.free(t_ref, flavor='raw')

            if janzone < julyzone:
                # DST is reversed in the southern hemisphere
                timezone = julyzone
                altzone = janzone
                daylight = int(janzone != julyzone)
                tzname = [julyname, janname]
            else:
                timezone = janzone
                altzone = julyzone
                daylight = int(janzone != julyzone)
                tzname = [janname, julyname]

        else:
            YEAR = (365 * 24 + 6) * 3600

            t = (((c_time(lltype.nullptr(rffi.TIME_TP.TO))) / YEAR) * YEAR)
            # we cannot have reference to stack variable, put it on the heap
            t_ref = lltype.malloc(rffi.TIME_TP.TO, 1, flavor='raw')
            t_ref[0] = rffi.cast(rffi.TIME_T, t)
            p = c_localtime(t_ref)
            janzone = -p.c_tm_gmtoff
            tm_zone = rffi.charp2str(p.c_tm_zone)
            janname = ["   ", tm_zone][bool(tm_zone)]
            tt = t + YEAR / 2
            t_ref[0] = rffi.cast(rffi.TIME_T, tt)
            p = c_localtime(t_ref)
            lltype.free(t_ref, flavor='raw')
            tm_zone = rffi.charp2str(p.c_tm_zone)
            julyzone = -p.c_tm_gmtoff
            julyname = ["   ", tm_zone][bool(tm_zone)]

            if janzone < julyzone:
                # DST is reversed in the southern hemisphere
                timezone = julyzone
                altzone = janzone
                daylight = int(janzone != julyzone)
                tzname = [julyname, janname]
            else:
                timezone = janzone
                altzone = julyzone
                daylight = int(janzone != julyzone)
                tzname = [janname, julyname]

    _set_time_attr(space, "TIMEZONE", space.newint(timezone))
    _set_time_attr(space, "DAYLIGHT", space.newint(daylight))
    tzname_w = [space.newstr_fromstr(tzname[0]), space.newstr_fromstr(tzname[1])]
    _set_time_attr(space, "TZNAME", space.newarray(tzname_w))
    _set_time_attr(space, "ALTZONE", space.newint(altzone))

def _get_error_msg():
    errno = rposix.get_errno()
    return os.strerror(errno)

if not system.IS_WINDOWS:
    def sleep(space, secs):
        if secs < 0:
            raise space.error(space.w_IOError,
                              "Invalid argument: negative time in sleep")
        pytime.sleep(secs)
else:
    from rpython.rlib import rwin32
    from errno import EINTR
    def _simple_sleep(space, secs, interruptible):
        if secs == 0.0 or not interruptible:
            pytime.sleep(secs)
        else:
            millisecs = int(secs * 1000)
            interrupt_event = space.fromcache(State).get_interrupt_event()
            rwin32.ResetEvent(interrupt_event)
            rc = rwin32.WaitForSingleObject(interrupt_event, millisecs)
            if rc == rwin32.WAIT_OBJECT_0:
                # Yield to make sure real Python signal handler
                # called.
                pytime.sleep(0.001)
                raise wrap_oserror(space,
                                   OSError(EINTR, "sleep() interrupted"))
    def sleep(space, secs):
        if secs < 0:
            raise space.error(space.w_IOError,
                              "Invalid argument: negative time in sleep")
        # as decreed by Guido, only the main thread can be
        # interrupted.
        main_thread = space.fromcache(State).main_thread
        interruptible = (main_thread == thread.get_ident())
        MAX = sys.maxint / 1000.0 # > 24 days
        while secs > MAX:
            _simple_sleep(space, MAX, interruptible)
            secs -= MAX
        _simple_sleep(space, secs, interruptible)

def _get_time_attr(space, obj_name):
    from topaz.objects.timeobject import W_TimeObject
    w_cls = space.getclassfor(W_TimeObject)
    return space.find_const(w_cls, obj_name)

def _set_time_attr(space, obj_name, w_obj_value):
    from topaz.objects.timeobject import W_TimeObject
    w_cls = space.getclassfor(W_TimeObject)
    space.set_const(w_cls, obj_name, w_obj_value)

def _get_inttime(space, w_seconds):
    # w_seconds can be a wrapped None (it will be automatically wrapped
    # in the callers, so we never get a real None here).
    if w_seconds is None:
        seconds = pytime.time()
    else:
        seconds = space.float_w(w_seconds)
    try:
        seconds = ovfcheck_float_to_int(seconds)
        t = rffi.r_time_t(seconds)
        if rffi.cast(lltype.Signed, t) != seconds:
            raise OverflowError
    except OverflowError:
        raise space.error(space.w_ArgumentError, "time argument too large")
    return t

def _tm_to_tuple(t):
    time_tuple = (
        rffi.getintfield(t, 'c_tm_year') + 1900,
        rffi.getintfield(t, 'c_tm_mon') + 1, # want january == 1
        rffi.getintfield(t, 'c_tm_mday'),
        rffi.getintfield(t, 'c_tm_hour'),
        rffi.getintfield(t, 'c_tm_min'),
        rffi.getintfield(t, 'c_tm_sec'),
        (rffi.getintfield(t, 'c_tm_wday') + 6) % 7, # want monday == 0
        rffi.getintfield(t, 'c_tm_yday') + 1, # want january, 1 == 1
        rffi.getintfield(t, 'c_tm_isdst')
    )

    return time_tuple

def _gettmarg(space, tup, allow_none=True):
    if tup is None:
        if not allow_none:
            raise space.error(space.w_TypeError, "tuple expected")
        # default to the current local time
        tt = rffi.r_time_t(int(pytime.time()))
        t_ref = lltype.malloc(rffi.TIME_TP.TO, 1, flavor='raw')
        t_ref[0] = tt
        pbuf = c_localtime(t_ref)
        lltype.free(t_ref, flavor='raw')
        if not pbuf:
            raise space.error(space.w_ArgumentError, _get_error_msg())
        return pbuf

    if len(tup) != 9:
        raise space.error(space.w_TypeError,
            "argument must be sequence of "
            "length 9, not %d" % len(tup)
        )

    y = tup[0]
    tm_mon = tup[1]
    if tm_mon == 0:
        tm_mon = 1
    tm_mday = tup[2]
    if tm_mday == 0:
        tm_mday = 1
    tm_yday = tup[7]
    if tm_yday == 0:
        tm_yday = 1
    rffi.setintfield(glob_buf, 'c_tm_mon', tm_mon)
    rffi.setintfield(glob_buf, 'c_tm_mday', tm_mday)
    rffi.setintfield(glob_buf, 'c_tm_hour', tup[3])
    rffi.setintfield(glob_buf, 'c_tm_min', tup[4])
    rffi.setintfield(glob_buf, 'c_tm_sec', tup[5])
    rffi.setintfield(glob_buf, 'c_tm_wday', tup[6])
    rffi.setintfield(glob_buf, 'c_tm_yday', tm_yday)
    rffi.setintfield(glob_buf, 'c_tm_isdst', tup[8])
    if system.IS_POSIX:
        if system.IS_CYGWIN:
            pass
        else:
            # actually never happens, but makes annotator happy
            glob_buf.c_tm_zone = lltype.nullptr(rffi.CCHARP.TO)
            rffi.setintfield(glob_buf, 'c_tm_gmtoff', 0)

    w_accept2dyear = _get_time_attr(space, "ACCEPT2DYEAR")
    accept2dyear = space.int_w(w_accept2dyear)

    if y < 1900:
        if not accept2dyear:
            raise space.error(space.w_ArgumentError, "year >= 1900 required")

        if 69 <= y <= 99:
            y += 1900
        elif 0 <= y <= 68:
            y += 2000
        else:
            raise space.error(space.w_ArgumentError, "year out of range")

    # tm_wday does not need checking of its upper-bound since taking "%
    #  7" in gettmarg() automatically restricts the range.
    if rffi.getintfield(glob_buf, 'c_tm_wday') < -1:
        raise space.error(space.w_ArgumentError, "day of week out of range")

    rffi.setintfield(glob_buf, 'c_tm_year', y - 1900)
    rffi.setintfield(glob_buf, 'c_tm_mon',
                     rffi.getintfield(glob_buf, 'c_tm_mon') - 1)
    rffi.setintfield(glob_buf, 'c_tm_wday',
                     (rffi.getintfield(glob_buf, 'c_tm_wday') + 1) % 7)
    rffi.setintfield(glob_buf, 'c_tm_yday',
                     rffi.getintfield(glob_buf, 'c_tm_yday') - 1)

    return glob_buf

time = pytime.time

## if system.IS_WINDOWS:
##     class PCCache:
##         pass
##     pccache = PCCache()
##     pccache.divisor = 0.0
##     pccache.ctrStart = 0

clock = pytime.clock

def ctime(space, w_seconds=None):
    """ctime([seconds]) -> string

    Convert a time in seconds since the Epoch to a string in local time.
    This is equivalent to asctime(localtime(seconds)). When the time tuple is
    not present, current time as returned by localtime() is used."""

    seconds = _get_inttime(space, w_seconds)

    t_ref = lltype.malloc(rffi.TIME_TP.TO, 1, flavor='raw')
    t_ref[0] = seconds
    p = c_ctime(t_ref)
    lltype.free(t_ref, flavor='raw')
    if not p:
        raise space.error(space.w_ArgumentError, "unconvertible time")

    return rffi.charp2str(p)[:-1] # get rid of new line

# by now w_tup is an optional argument (and not *args)
# because of the ext. compiler bugs in handling such arguments (*args, **kwds)
def asctime(space, w_tup=None):
    """asctime([tuple]) -> string

    Convert a time tuple to a string, e.g. 'Sat Jun 06 16:26:11 1998'.
    When the time tuple is not present, current time as returned by localtime()
    is used."""
    buf_value = _gettmarg(space, w_tup)
    p = c_asctime(buf_value)
    if not p:
        raise space.error(space.w_ArgumentError, "unconvertible time")

    return rffi.charp2str(p)[:-1] # get rid of new line

def gmtime(space, w_seconds=None):
    """gmtime([seconds]) -> (tm_year, tm_mon, tm_day, tm_hour, tm_min,
                          tm_sec, tm_wday, tm_yday, tm_isdst)

    Convert seconds since the Epoch to a time tuple expressing UTC (a.k.a.
    GMT).  When 'seconds' is not passed in, convert the current time instead.
    """

    # rpython does not support that a variable has two incompatible builtins
    # as value so we have to duplicate the code. NOT GOOD! see localtime() too
    seconds = _get_inttime(space, w_seconds)
    t_ref = lltype.malloc(rffi.TIME_TP.TO, 1, flavor='raw')
    t_ref[0] = seconds
    p = c_gmtime(t_ref)
    lltype.free(t_ref, flavor='raw')

    if not p:
        raise space.error(space.w_ArgumentError, _get_error_msg())
    return _tm_to_tuple(p)

def localtime(space, w_seconds=None):
    """localtime([seconds]) -> (tm_year, tm_mon, tm_day, tm_hour, tm_min,
                             tm_sec, tm_wday, tm_yday, tm_isdst)

    Convert seconds since the Epoch to a time tuple expressing local time.
    When 'seconds' is not passed in, convert the current time instead."""

    seconds = _get_inttime(space, w_seconds)
    t_ref = lltype.malloc(rffi.TIME_TP.TO, 1, flavor='raw')
    t_ref[0] = seconds
    p = c_localtime(t_ref)
    lltype.free(t_ref, flavor='raw')

    if not p:
        raise space.error(space.w_ArgumentError, _get_error_msg())
    return _tm_to_tuple(p)

def mktime(space, tup):
    """mktime(tuple) -> floating point number

    Convert a time tuple in local time to seconds since the Epoch."""

    buf = _gettmarg(space, tup, allow_none=False)
    rffi.setintfield(buf, "c_tm_wday", -1)
    tt = c_mktime(buf)
    # A return value of -1 does not necessarily mean an error, but tm_wday
    # cannot remain set to -1 if mktime succeeds.
    if tt == -1 and rffi.getintfield(buf, "c_tm_wday") == -1:
        raise space.error(space.w_ArgumentError, "mktime argument out of range")

    return float(tt)

if system.IS_POSIX:
    def tzset(space):
        """tzset()

        Initialize, or reinitialize, the local timezone to the value stored in
        os.environ['TZ']. The TZ environment variable should be specified in
        standard Unix timezone format as documented in the tzset man page
        (eg. 'US/Eastern', 'Europe/Amsterdam'). Unknown timezones will silently
        fall back to UTC. If the TZ environment variable is not set, the local
        timezone is set to the systems best guess of wallclock time.
        Changing the TZ environment variable without calling tzset *may* change
        the local timezone used by methods such as localtime, but this behaviour
        should not be relied on"""

        c_tzset()

        # reset timezone, altzone, daylight and tzname
        _init_timezone(space)

def strftime(space, format, tup=None):
    """strftime(format[, tuple]) -> string

    Convert a time tuple to a string according to a format specification.
    See the library reference manual for formatting codes. When the time tuple
    is not present, current time as returned by localtime() is used."""
    buf_value = _gettmarg(space, tup)

    # Checks added to make sure strftime() does not crash Python by
    # indexing blindly into some array for a textual representation
    # by some bad index (fixes bug #897625).
    # No check for year since handled in gettmarg().
    if rffi.getintfield(buf_value, 'c_tm_mon') < 0 or rffi.getintfield(buf_value, 'c_tm_mon') > 11:
        raise space.error(space.w_ArgumentError, "month out of range")
    if rffi.getintfield(buf_value, 'c_tm_mday') < 1 or rffi.getintfield(buf_value, 'c_tm_mday') > 31:
        raise space.error(space.w_ArgumentError, "day of month out of range")
    if rffi.getintfield(buf_value, 'c_tm_hour') < 0 or rffi.getintfield(buf_value, 'c_tm_hour') > 23:
        raise space.error(space.w_ArgumentError, "hour out of range")
    if rffi.getintfield(buf_value, 'c_tm_min') < 0 or rffi.getintfield(buf_value, 'c_tm_min') > 59:
        raise space.error(space.w_ArgumentError, "minute out of range")
    if rffi.getintfield(buf_value, 'c_tm_sec') < 0 or rffi.getintfield(buf_value, 'c_tm_sec') > 61:
        raise space.error(space.w_ArgumentError, "seconds out of range")
    if rffi.getintfield(buf_value, 'c_tm_yday') < 0 or rffi.getintfield(buf_value, 'c_tm_yday') > 365:
        raise space.error(space.w_ArgumentError, "day of year out of range")
    if rffi.getintfield(buf_value, 'c_tm_isdst') < -1 or rffi.getintfield(buf_value, 'c_tm_isdst') > 1:
        raise space.error(space.w_ArgumentError, "daylight savings flag out of range")

    if system.IS_WINDOWS:
        # check that the format string contains only valid directives
        length = len(format)
        i = 0
        while i < length:
            if format[i] == '%':
                i += 1
                if i < length and format[i] == '#':
                    # not documented by python
                    i += 1
                if i >= length or format[i] not in "aAbBcdHIjmMpSUwWxXyYzZ%":
                    raise space.error(space.w_ArgumentError, "invalid format string")
            i += 1

    i = 1024
    while True:
        outbuf = lltype.malloc(rffi.CCHARP.TO, i, flavor='raw')
        try:
            buflen = c_strftime(outbuf, i, format, buf_value)
            if buflen > 0 or i >= 256 * len(format):
                # if the buffer is 256 times as long as the format,
                # it's probably not failing for lack of room!
                # More likely, the format yields an empty result,
                # e.g. an empty format, or %Z when the timezone
                # is unknown.
                return rffi.charp2strn(outbuf, intmask(buflen))
        finally:
            lltype.free(outbuf, flavor='raw')
        i += i
