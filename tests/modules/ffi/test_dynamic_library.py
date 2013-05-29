from tests.base import BaseTopazTest
from topaz.modules.ffi.dynamic_library import W_DynamicLibraryObject
from rpython.rlib import clibffi

class TestDynamicLibrary(BaseTopazTest):

    def test_consts(self, space):
        consts = {'LAZY':1 , 'NOW':2, 'GLOBAL':257, 'LOCAL':0}
        for name in consts:
            w_res = space.execute('FFI::DynamicLibrary::RTLD_%s' % name)
            space.int_w(w_res) == consts[name]

    def test_open(self, space):
        w_res = space.execute("FFI::DynamicLibrary.open('libm.so', 1)")
        assert isinstance(w_res, W_DynamicLibraryObject)
        assert w_res.handle == clibffi.dlopen('libm.so', 1)
        w_name = space.find_instance_var(w_res, '@name')
        assert self.unwrap(space, w_name) == 'libm.so'
        w_res = space.execute("FFI::DynamicLibrary.open('libm.so', 0)")
        assert w_res.handle == clibffi.dlopen('libm.so', 0)
        w_res = space.execute("FFI::DynamicLibrary.open(nil, 2)")
        assert w_res.handle == clibffi.dlopen(None, 2)
        w_name = space.find_instance_var(w_res, '@name')
        assert self.unwrap(space, w_name) == '[current process]'
        with self.raises(space, "TypeError", "can't convert Float into String"):
            space.execute("FFI::DynamicLibrary.open(3.142, 1)")
        # The next error message is different from the one in ruby 1.9.3.
        # But the meaning is the same.
        with self.raises(space, "TypeError", "can't convert String into Integer"):
            space.execute("FFI::DynamicLibrary.open('something', 'invalid flag')")

    def test_open_error(self, space):
        with self.raises(space, "LoadError",
                         "Could not open library wrong_name.so"):
            space.execute("FFI::DynamicLibrary.open('wrong_name.so')")

    def test_new_same_as_open(self, space):
        w_lib1 = space.execute("FFI::DynamicLibrary.new('libm.so')")
        w_lib2 = space.execute("FFI::DynamicLibrary.open('libm.so')")
        assert w_lib1.handle == w_lib2.handle

    def test_Symbol(self, space):
        w_lib_sym = space.execute("FFI::DynamicLibrary::Symbol")
        assert w_lib_sym != space.w_symbol

    def test_Symbol_null_p(self, space):
        w_res = space.execute("FFI::DynamicLibrary::Symbol.new.null?")
        assert self.unwrap(space, w_res)

    def test_find_variable(self, space):
        w_dl_sym = space.execute("FFI::DynamicLibrary::Symbol")
        w_res = space.execute("""
        FFI::DynamicLibrary.new('libm.so').find_variable(:sin)
        """)
        assert w_res.getclass(space) is w_dl_sym

    def test_find_function(self, space):
        w_actual = space.execute("""
        FFI::DynamicLibrary.new('libm.so').find_variable(:exp)
        """)
        w_expected = space.execute("""
        FFI::DynamicLibrary.new('libm.so').find_function(:exp)
        """)
        assert w_actual.getclass(space) == w_expected.getclass(space)
