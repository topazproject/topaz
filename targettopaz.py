from rpython.jit.codewriter.policy import JitPolicy

from topaz.main import create_entry_point, get_topaz_config_options


def target(driver, args):
    driver.exe_name = "bin/topaz"
    driver.config.set(**get_topaz_config_options())
    return create_entry_point(driver.config), None


def jitpolicy(driver):
    return JitPolicy()


def handle_config(config, translateconfig):
    from rpython.translator.platform import host_factory
    max_stack_size = 11 << 18 # 2.8 Megs
    if host_factory.name == 'msvc':
        host_factory.cflags += ('/DMAX_STACK_SIZE=%d' % max_stack_size,)
    elif host_factory.name in ('linux', 'darwin'):
        host_factory.cflags += ('-DMAX_STACK_SIZE=%d' % max_stack_size,)
    config.translation.suggest(check_str_without_nul=True)
