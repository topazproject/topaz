from pypy.jit.codewriter.policy import JitPolicy

from rupypy.main import create_entry_point, get_topaz_config_options


def target(driver, args):
    driver.exe_name = "topaz-c"
    driver.config.set(**get_topaz_config_options())
    return create_entry_point(driver.config), None


def jitpolicy(driver):
    return JitPolicy()
