from tests.modules.ffi.base import BaseFFITest

from rpython.rtyper.lltypesystem import rffi

# Most of the stuff is still very vague.
# This is because lots of the constants had to be set to something in order to
# run some specs but the specs weren't about them.
class TestTypeDefs(BaseFFITest):
    def test_it_is_kind_of_a_Hash(self, space):
        assert self.ask(space, 'FFI::TypeDefs.kind_of? Hash')

class TestTypes(BaseFFITest):
    def test_it_is_kind_of_a_Hash(self, space):
        assert self.ask(space, 'FFI::Types.kind_of? Hash')

class TestPlatform(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::Platform.is_a? Module")

    def test_it_offers_some_SIZE_constants(self, space):
        w_res = space.execute('FFI::Platform::INT8_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.CHAR)
        w_res = space.execute('FFI::Platform::INT16_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.SHORT)
        w_res = space.execute('FFI::Platform::INT32_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.INT)
        w_res = space.execute('FFI::Platform::INT64_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.LONGLONG)
        w_res = space.execute('FFI::Platform::LONG_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.LONG)
        w_res = space.execute('FFI::Platform::FLOAT_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.FLOAT)
        w_res = space.execute('FFI::Platform::DOUBLE_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.DOUBLE)
        w_res = space.execute('FFI::Platform::ADDRESS_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.VOIDP)

class TestStructLayout(BaseFFITest):
    def test_it_is_a_class(self, space):
        assert self.ask(space, "FFI::StructLayout.is_a? Class")

    def test_its_Field_constant_is_nil(self, space):
        assert self.ask(space, "FFI::StructLayout::Field.nil?")

class TestStructByReference(BaseFFITest):
    def test_it_is_a_class(self, space):
        assert self.ask(space, "FFI::StructByReference.is_a? Class")

class TestNullPointerError(BaseFFITest):
    def test_it_inherits_from_Exception(self, space):
        assert self.ask(space,
        "FFI::NullPointerError.ancestors.include? Exception")
