from rpython.jit.codewriter.policy import JitPolicy

from topaz.main import entry_point


def target(driver, args):
    driver.exe_name = "bin/topaz"
    return entry_point, None


def jitpolicy(driver):
    return JitPolicy()
