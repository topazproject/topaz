from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.dynamic_library import W_DL_SymbolObject

from rpython.rlib import clibffi

import sys

if sys.platform == 'darwin':
    libm = 'libm.dylib'
else:
    libm = 'libm.so'

class TestDynamicLibrary(BaseFFITest):
    def test_consts(self, space):
        consts = {'LAZY':1 , 'NOW':2, 'GLOBAL':257, 'LOCAL':0}
        for name in consts:
            w_res = space.execute('FFI::DynamicLibrary::RTLD_%s' % name)
            space.int_w(w_res) == consts[name]

class TestDynamicLibrary__new(BaseFFITest):
    def test_it_opens_a_dynamic_library(self, space):
        w_res = space.execute("FFI::DynamicLibrary.new('%s', 1)" % libm)
        assert w_res.cdll.lib == clibffi.dlopen(libm, 1)
        w_res = space.execute("FFI::DynamicLibrary.new('%s', 0)" % libm)
        assert w_res.cdll.lib == clibffi.dlopen(libm, 0)

    def test_it_stores_the_name_of_the_opened_lib(self, space):
        w_res = space.execute("FFI::DynamicLibrary.new('%s', 1)" % libm)
        w_name = space.find_instance_var(w_res, '@name')
        assert self.unwrap(space, w_name) == libm

    def test_it_accepts_nil_as_library_name(self, space):
        w_res = space.execute("FFI::DynamicLibrary.new(nil, 2)")
        assert w_res.cdll.lib == clibffi.dlopen(None, 2)
        w_name = space.find_instance_var(w_res, '@name')
        assert self.unwrap(space, w_name) == '[current process]'

    def test_it_does_not_accept_anything_else_as_lib_name(self, space):
        with self.raises(space, "TypeError", "can't convert Float into String"):
            space.execute("FFI::DynamicLibrary.new(3.142, 1)")

    def test_it_only_accepts_an_integer_as_flag_parameter(self, space):
        # The next error message is different from the one in ruby 1.9.3.
        # But the meaning is the same.
        with self.raises(space, "TypeError", "can't convert String into Integer"):
            space.execute("FFI::DynamicLibrary.new('something', 'invalid flag')")

    def test_it_raises_a_LoadError_if_it_can_not_find_the_library(self, space):
        with self.raises(space, "LoadError",
                         "Could not open library wrong_name.so"):
            space.execute("FFI::DynamicLibrary.new('wrong_name.so')")

    def test_it_also_known_as_open(self, space):
        assert self.ask(space, "FFI::DynamicLibrary.method(:new) =="
                               "FFI::DynamicLibrary.method(:open)")

class TestDynamicLibrary__Symbol(BaseFFITest):
    def test_its_a_wrapper_around_a_function_symbol(self, space):
        exp_ptr = clibffi.CDLL( libm).getaddressindll('exp')
        w_dl_sym = W_DL_SymbolObject(space, exp_ptr)
        assert w_dl_sym.ptr == exp_ptr

class TestDynamicLibrary_find_variable(BaseFFITest):
    def test_it_returns_a_DynamicLibrary__Symbol(self, space):
        w_dl_sym = space.execute("FFI::DynamicLibrary::Symbol")
        w_res = space.execute("""
        FFI::DynamicLibrary.new('%s').find_variable(:sin)
        """ % libm)
        assert w_res.getclass(space) is w_dl_sym

    def test_it_also_known_as_find_function(self, space):
        assert self.ask(space, """
        dl = FFI::DynamicLibrary.new('%s')
        dl.method(:find_function) == dl.method(:find_variable)
        """ % libm) 
