from rpython.jit.codewriter.policy import JitPolicy

from topaz.main import entry_point


def target(driver, args):
    driver.exe_name = "bin/topaz"
    config = driver.config
    config.translation.suggest(check_str_without_nul=True)
    return entry_point, None


def jitpolicy(driver):
    return JitPolicy()
