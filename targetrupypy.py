from pypy.jit.codewriter.policy import JitPolicy

from rupypy.main import entry_point


def target(driver, args):
    driver.exe_name = "./bin/topaz"
    return entry_point, None


def jitpolicy(driver):
    return JitPolicy()
