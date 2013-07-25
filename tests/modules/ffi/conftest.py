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
    ffis.execute("""
    class Symbol
        def eql?(other)
            self.to_s == other.to_s
        end
        def hash
            self.to_s.hash - 10000
        end
    end
    """)
    cp = copy.deepcopy(ffis)
    return cp

def pytest_funcarg__libtest_so():
    self_dir = os.path.join(os.path.dirname(__file__))
    rel_to_makefile = os.path.join('libtest', 'GNUmakefile')
    makefile = os.path.abspath(os.path.join(self_dir, rel_to_makefile))
    os.system("make -f " + makefile)
    rel_to_libtest_so = os.path.join('build', 'libtest.so')
    libtest_so = os.path.abspath(os.path.join(self_dir, rel_to_libtest_so))
    return libtest_so
