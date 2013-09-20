import os

from rpython.rtyper.lltypesystem.ll2ctypes import ALLOCATED

def pytest_funcarg__ffis(request, space):
    system, _, _, _, cpu = os.uname() # not for windows
    space.execute("""
    RUBY_ENGINE = 'topaz'
    RUBY_PLATFORM = '%s-%s'
    load 'ffi.rb'
    """ % (cpu, system.lower()))
    return space

def pytest_funcarg__libtest_so():
    self_dir = os.path.join(os.path.dirname(__file__))
    rel_to_makefile = os.path.join('libtest', 'GNUmakefile')
    makefile = os.path.abspath(os.path.join(self_dir, rel_to_makefile))
    os.system("make -f " + makefile)
    rel_to_libtest_so = os.path.join('build', 'libtest.so')
    libtest_so = os.path.abspath(os.path.join(self_dir, rel_to_libtest_so))
    return libtest_so
