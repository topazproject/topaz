import copy
import os

from rpython.config.translationoption import get_combined_translation_config
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

def pytest_runtest_setup(item):
    item.len_ALLOCATED = len(ALLOCATED)

def pytest_runtest_teardown(item):
    if len(ALLOCATED) != item.len_ALLOCATED:
        print ("Warning: Something allocated in test %s is still allocated:"
               % item)
        print ALLOCATED
