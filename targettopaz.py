from pypy.jit.codewriter.policy import JitPolicy

from topaz.main import entry_point


def target(driver, args):
    driver.exe_name = "topaz-c"
    return entry_point, None


def jitpolicy(driver):
    return JitPolicy()
