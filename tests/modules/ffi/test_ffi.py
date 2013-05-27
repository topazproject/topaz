from tests.base import BaseTopazTest
from topaz.modules.ffi import FFI
from topaz.modules.ffi.type import W_TypeObject
from rpython.rlib import clibffi
from topaz.objects.hashobject import W_HashObject
from topaz.objects.classobject import W_ClassObject
from topaz.objects.moduleobject import W_ModuleObject
from rpython.rtyper.lltypesystem import rffi

class TestFFI(BaseTopazTest):

    primitive_types =  ['INT8', 'UINT8', 'INT16', 'UINT16',
                        'INT32', 'UINT32', 'INT64', 'UINT64',
                        'LONG', 'ULONG', 'FLOAT32', 'FLOAT64',
                        'VOID', 'LONGDOUBLE', 'POINTER', 'BOOL',
                        'VARARGS']
    alias_types = {'SCHAR': 'INT8',
                   'CHAR' : 'INT8',
                   'UCHAR' : 'UINT8',
                   'SHORT' : 'INT16',
                   'SSHORT' : 'INT16',
                   'USHORT' : 'UINT16',
                   'INT' : 'INT32',
                   'SINT' : 'INT32',
                   'UINT' : 'UINT32',
                   'LONG_LONG' : 'INT64',
                   'SLONG' : 'LONG',
                   'SLONG_LONG' : 'INT64',
                   'ULONG_LONG' : 'UINT64',
                   'FLOAT' : 'FLOAT32',
                   'DOUBLE' : 'FLOAT64',
                   'STRING' : 'POINTER',
                   'BUFFER_IN' : 'POINTER',
                   'BUFFER_OUT' : 'POINTER',
                   'BUFFER_INOUT' : 'POINTER'}

    def test_basic(self, space):
        w_type_defs = space.execute('FFI::TypeDefs')
        assert isinstance(w_type_defs, W_HashObject)
        w_types = space.execute('FFI::Types')
        assert isinstance(w_types, W_HashObject)

    def test_FFI_type_constants(self, space):
        # just check, whether the constants even exist for now
        for pt in TestFFI.primitive_types:
            space.execute('FFI::TYPE_%s' % pt)

    def test_NativeType(self, space):
        w_native_type = space.execute('FFI::NativeType')
        assert isinstance(w_native_type, W_ModuleObject)
        for pt in TestFFI.primitive_types:
            space.execute('FFI::NativeType::%s' %pt)

    def test_Type_ll(self, space):
        w_type = W_TypeObject(space, 'TESTVOID', clibffi.ffi_type_void)
        assert w_type.native_type == 'TESTVOID'
        assert w_type.ffi_type is clibffi.ffi_type_void

    def test_Type(self, space):
        w_type = space.execute('FFI::Type')
        assert isinstance(w_type, W_ClassObject)

    def test_Builtin(self, space):
        w_builtin = space.execute('FFI::Type::Builtin')
        assert isinstance(w_builtin, W_ClassObject)
        w_type = space.execute('FFI::Type')
        assert w_builtin.superclass is w_type

    def test_Builtin_instances(self, space):
        for pt in TestFFI.primitive_types:
            w_ac = space.execute('FFI::Type::%s' %pt)
            w_ex = space.execute('FFI::NativeType::%s' % pt)
            assert self.unwrap(space, w_ac) == self.unwrap(space, w_ex)
        for at in TestFFI.alias_types:
            w_ac = space.execute('FFI::Type::%s' %at)
            w_ex = space.execute('FFI::Type::%s' %TestFFI.alias_types[at])
            assert self.unwrap(space, w_ac) == self.unwrap(space, w_ex)
        w_mapped = space.execute('FFI::Type::Mapped')
        assert isinstance(w_mapped, W_ClassObject)
        w_res = space.execute('FFI::Type::Mapped.respond_to? :method_missing')
        assert self.unwrap(space, w_res)
        w_res = space.execute('FFI::Type::Mapped.new(42)')

    def test_Platform(self, space):
        w_p = space.execute('FFI::Platform')
        assert type(w_p) is W_ModuleObject
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

    def test_StructLayout(self, space):
        w_sl = space.execute('FFI::StructLayout')
        assert isinstance(w_sl, W_ClassObject)
        w_res = space.execute('FFI::StructLayout::Field')
        assert w_res == space.w_nil

    def test_StructByReference(self, space):
        w_sbr = space.execute('FFI::StructByReference')
        assert isinstance(w_sbr, W_ClassObject)
