from rpython.jit.codewriter.policy import JitPolicy

from topaz.main import entry_point


def target(driver, args):
    driver.exe_name = "bin/topaz"
    return entry_point, None


def jitpolicy(driver):
    return JitPolicy()


def handle_config(config, translateconfig):
    config.translation.suggest(check_str_without_nul=True)
