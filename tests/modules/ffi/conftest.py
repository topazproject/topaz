import copy
import os

def pytest_funcarg__ffi_space(request, space):
    def build_ffi_space():
        ffi_space = copy.deepcopy(space)
        system, _, _, _, cpu = os.uname() # not for windows
        ffi_space.execute("""
        RUBY_ENGINE = 'topaz'
        RUBY_PLATFORM = '%s-%s'
        load 'ffi.rb'
        """ % (cpu, system.lower()))
        return ffi_space

    ffi_space = request.cached_setup(
        setup=build_ffi_space,
        scope="session",
    )
    return copy.deepcopy(ffi_space)
