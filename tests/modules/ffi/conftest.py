import copy
import os

def pytest_funcarg__ffis(request, space):
    def build_ffis():
        ffis = copy.deepcopy(space)
        system, _, _, _, cpu = os.uname() # not for windows
        ffis.execute("""
        RUBY_ENGINE = 'topaz'
        RUBY_PLATFORM = '%s-%s'
        load 'ffi.rb'
        """ % (cpu, system.lower()))
        return ffis

    ffis = request.cached_setup(
        setup=build_ffis,
        scope="session",
    )
    return copy.deepcopy(ffis)
