from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.type import (type_names, rw_strategies,
                                    W_TypeObject, VOID)
from topaz.modules.ffi import type as ffitype

from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi, lltype

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

class TestType(BaseFFITest):
    def test_it_is_a_class(self, space):
        assert self.ask(space, "FFI::Type.is_a? Class")

    def test_builtin_is_a_type_subclass(self, space):
        w_res = space.execute("FFI::Type::Builtin.ancestors")
        w_type = space.execute("FFI::Type")
        assert w_type in self.unwrap(space, w_res)

    def test_it_has_these_attributes_on_the_low_level(self, space):
        w_type = W_TypeObject(space, 123)
        assert w_type.typeindex == 123

    def test_it_delegates_read_and_write_to_rw_strategy(self, space):
        # only works in Python unit test because of dynamic typing
        class RWStrategyMock(object):
            def read(self, space, data):
                return "read with data = %s" %data
            def write(self, space, data, w_obj):
                return "write with data = %s and w_obj = %s" %(data, w_obj)
        w_type = W_TypeObject(space)
        w_type.rw_strategy = RWStrategyMock()
        assert w_type.read(space, "foo") == "read with data = foo"
        assert (w_type.write(space, "bar", 5) ==
                "write with data = bar and w_obj = 5")

class TestFFI__TestType(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::NativeType.is_a? Module")

    def test_it_contains_some_type_constants(self, space):
        for t in rw_strategies:
            typename = type_names[t]
            assert self.ask(space, "FFI::NativeType::%s.is_a? FFI::Type"
                            %typename)

    def test_it_has_these_instances_defined_as_constants(self, space):
        for t in rw_strategies:
            typename = type_names[t]
            assert self.ask(space, "FFI::Type::%s.is_a? FFI::Type"
                            % typename)
            assert self.ask(space, "FFI::Type::%s.is_a? FFI::Type::Builtin"
                            % typename)

    def test_its_instances_can_be_accessed_in_different_ways(self, space):
        for t in rw_strategies:
            typename = type_names[t]
            w_t1 = space.execute('FFI::TYPE_%s' % typename)
            w_t2 = space.execute('FFI::Type::%s' % typename)
            w_t3 = space.execute('FFI::NativeType::%s' % typename)
            assert w_t1 == w_t2
            assert w_t2 == w_t3

class TestFFI__Type_size(BaseFFITest):
    def test_it_returns_the_size_type(self, space):
        w_res = space.execute("FFI::Type::INT8.size")
        assert self.unwrap(space, w_res) == 1
        w_res = space.execute("FFI::Type::INT16.size")
        assert self.unwrap(space, w_res) == 2
        w_res = space.execute("FFI::Type::INT32.size")
        assert self.unwrap(space, w_res) == 4

class TestFFI__Type_eq(BaseFFITest):
    def test_it_compares_the_names(self, space):
        type1 = W_TypeObject(space, VOID)
        type2 = W_TypeObject(space, VOID)
        w_assertion = space.send(type1, '==', [type2])
        assert self.unwrap(space, w_assertion)

class Test_StringRWStrategy(BaseFFITest):
    def test_it_reads_a_string_from_buffer(self, space):
        w_string_type = ffitype.StringRWStrategy()
        size = w_string_type.typesize
        data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        raw_str = rffi.str2charp("test")
        misc.write_raw_unsigned_data(data, raw_str, size)
        w_res = w_string_type.read(space, data)
        assert space.is_kind_of(w_res, space.w_string)
        assert self.unwrap(space, w_res) == "test"
        lltype.free(data, flavor='raw')

    def test_it_writes_a_string_to_buffer(self, space):
        w_string_type = ffitype.StringRWStrategy()
        size = w_string_type.typesize
        data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        w_str = space.newstr_fromstr("test")
        w_string_type.write(space, data, w_str)
        raw_res = misc.read_raw_unsigned_data(data, size)
        raw_res = rffi.cast(rffi.CCHARP, raw_res)
        assert rffi.charp2str(raw_res) == "test"
        lltype.free(data, flavor='raw')

class Test_PointerRWStrategy(BaseFFITest):
    def test_it_reads_a_pointer_from_buffer(self, space):
        w_pointer_type = ffitype.PointerRWStrategy()
        size = w_pointer_type.typesize
        data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        raw_ptr = rffi.cast(lltype.Unsigned, 12)
        misc.write_raw_unsigned_data(data, raw_ptr, size)
        w_res = w_pointer_type.read(space, data)
        w_pointer_class = space.execute("FFI::Pointer")
        assert space.is_kind_of(w_res, w_pointer_class)
        assert self.unwrap(space, space.send(w_res, 'address')) == 12

    def test_it_writes_a_pointer_to_buffer(self, space):
        w_pointer_type = ffitype.PointerRWStrategy()
        size = w_pointer_type.typesize
        data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        w_ptr = space.execute("FFI::Pointer.new(15)")
        w_pointer_type.write(space, data, w_ptr)
        raw_res = misc.read_raw_unsigned_data(data, size)
        raw_res = rffi.cast(lltype.Unsigned, raw_res)
        assert raw_res == 15
        lltype.free(data, flavor='raw')

class Test_BoolRWStrategy(BaseFFITest):
    def test_it_reads_a_bool_from_buffer(self, space):
        w_bool_type = ffitype.BoolRWStrategy()
        size = w_bool_type.typesize
        data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        misc.write_raw_unsigned_data(data, False, size)
        w_res = w_bool_type.read(space, data)
        assert not space.is_true(w_res)
        lltype.free(data, flavor='raw')

    def test_it_writes_a_bool_to_buffer(self, space):
        w_bool_type = ffitype.BoolRWStrategy()
        size = w_bool_type.typesize
        data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        w_true = space.execute("true")
        w_bool_type.write(space, data, w_true)
        raw_res = misc.read_raw_unsigned_data(data, size)
        assert bool(raw_res)
        lltype.free(data, flavor='raw')

class Test_FloatRWStrategy(BaseFFITest):
    def test_it_reads_a_float32_to_buffer(self, space):
        w_float32_type = ffitype.FloatRWStrategy(ffitype.FLOAT32)
        data = lltype.malloc(rffi.CCHARP.TO, 4, flavor='raw')
        misc.write_raw_float_data(data, 1.25, 4)
        w_res = w_float32_type.read(space, data)
        assert self.unwrap(space, w_res) == 1.25
        lltype.free(data, flavor='raw')

    def test_it_reads_a_float64_to_buffer(self, space):
        w_float64_type = ffitype.FloatRWStrategy(ffitype.FLOAT64)
        data = lltype.malloc(rffi.CCHARP.TO, 8, flavor='raw')
        misc.write_raw_float_data(data, 1e-10, 8)
        w_res = w_float64_type.read(space, data)
        assert self.unwrap(space, w_res) == 1e-10
        lltype.free(data, flavor='raw')

    def test_it_writes_a_float32_to_buffer(self, space):
        w_float32_type = ffitype.FloatRWStrategy(ffitype.FLOAT32)
        data = lltype.malloc(rffi.CCHARP.TO, 4, flavor='raw')
        w_f = space.newfloat(3.75)
        w_float32_type.write(space, data, w_f)
        raw_res = misc.read_raw_float_data(data, 4)
        assert raw_res == 3.75
        lltype.free(data, flavor='raw')

    def test_it_writes_a_float64_to_buffer(self, space):
        w_float64_type = ffitype.FloatRWStrategy(ffitype.FLOAT64)
        data = lltype.malloc(rffi.CCHARP.TO, 8, flavor='raw')
        w_f = space.newfloat(1e-12)
        w_float64_type.write(space, data, w_f)
        raw_res = misc.read_raw_float_data(data, 8)
        assert raw_res == 1e-12
        lltype.free(data, flavor='raw')

class Test_SignedRWStrategy(BaseFFITest):
    def test_it_reads_signed_types_to_buffer(self, space):
        for t in [ffitype.INT8,
                  ffitype.INT16,
                  ffitype.INT32,
                  ffitype.INT64,
                  ffitype.LONG]:
            w_signed_type = ffitype.SignedRWStrategy(t)
            size = w_signed_type.typesize
            # make new buffer for every t
            data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
            misc.write_raw_signed_data(data, -88, size)
            w_res = w_signed_type.read(space, data)
            assert self.unwrap(space, w_res) == -88
            lltype.free(data, flavor='raw')

    def test_it_writes_signed_types_to_buffer(self, space):
        for t in [ffitype.INT8,
                  ffitype.INT16,
                  ffitype.INT32,
                  ffitype.INT64,
                  ffitype.LONG]:
            w_signed_type = ffitype.SignedRWStrategy(t)
            size = w_signed_type.typesize
            # make new buffer for every t
            data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
            w_i = space.newint(-18)
            w_signed_type.write(space, data, w_i)
            raw_res = misc.read_raw_signed_data(data, size)
            assert raw_res == -18
            lltype.free(data, flavor='raw')

class Test_UnsignedRWStrategy(BaseFFITest):
    def test_it_reads_unsigned_types_to_buffer(self, space):
        for t in [ffitype.UINT8,
                  ffitype.UINT16,
                  ffitype.UINT32,
                  ffitype.UINT64,
                  ffitype.ULONG]:
            w_unsigned_type = ffitype.UnsignedRWStrategy(t)
            size = w_unsigned_type.typesize
            # make new buffer for every t
            data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
            misc.write_raw_unsigned_data(data, 42, size)
            w_res = w_unsigned_type.read(space, data)
            assert self.unwrap(space, w_res) == 42
            lltype.free(data, flavor='raw')

    def test_it_writes_unsigned_types_to_buffer(self, space):
        for t in [ffitype.UINT8,
                  ffitype.UINT16,
                  ffitype.UINT32,
                  ffitype.UINT64,
                  ffitype.ULONG]:
            w_unsigned_type = ffitype.UnsignedRWStrategy(t)
            size = w_unsigned_type.typesize
            # make new buffer for every t
            data = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
            w_i = space.newint(16)
            w_unsigned_type.write(space, data, w_i)
            raw_res = misc.read_raw_unsigned_data(data, size)
            assert raw_res == 16
            lltype.free(data, flavor='raw')

class Test_VoidRWStrategy(BaseFFITest):
    def test_it_reads_nothing_and_returns_nil(self, space):
        data = lltype.malloc(rffi.CCHARP.TO, 1, flavor='raw')
        w_void_type = ffitype.VoidRWStrategy()
        w_res = w_void_type.read(space, data)
        assert self.unwrap(space, w_res) == None
        lltype.free(data, flavor='raw')

    def test_it_writes_nothing_and_returns_None(self, space):
        data = lltype.malloc(rffi.CCHARP.TO, 1, flavor='raw')
        misc.write_raw_signed_data(data, 11, 1)
        w_void_type = ffitype.VoidRWStrategy()
        res = w_void_type.write(space, data, 0)
        assert misc.read_raw_signed_data(data, 1) == 11
        assert res is None
        lltype.free(data, flavor='raw')

class TestFFI__Type__MappedObject(BaseFFITest):
    def test_its_superclass_is_Type(self, space):
        assert self.ask(space, "FFI::Type::Mapped.superclass.equal? FFI::Type")

class TestFFI__Type__MappedObject__new(BaseFFITest):
    def test_it_takes_a_data_converter_as_argument(self, space):
        with self.raises(space, "NoMethodError",
                         "native_type method not implemented"):
            space.execute("FFI::Type::Mapped.new(0)")
        with self.raises(space, "NoMethodError",
                         "to_native method not implemented"):
            space.execute("""
            class DataConverter
              def native_type; nil; end
            end
            FFI::Type::Mapped.new(DataConverter.new)
            """)
        with self.raises(space, "NoMethodError",
                         "from_native method not implemented"):
            space.execute("""
            class DataConverter
              def native_type; nil; end
              def to_native; nil; end
            end
            FFI::Type::Mapped.new(DataConverter.new)
            """)
        w_res = space.execute("""
        class DataConverter
          def native_type; FFI::Type::VOID; end
          def to_native; nil; end
          def from_native; nil; end
        end
        FFI::Type::Mapped.new(DataConverter.new)
        """)
        assert space.getclass(w_res.w_data_converter).name == 'DataConverter'

    def test_it_derives_the_typeindex_from_the_data_converter(self, space):
        w_res = space.execute("""
        class DataConverter
          def native_type
            FFI::Type::UINT16
          end
          def to_native; nil; end
          def from_native; nil; end
        end
        FFI::Type::Mapped.new(DataConverter.new)
        """)
        assert type_names[w_res.typeindex] == "UINT16"
        with self.raises(space, "TypeError",
                         "native_type did not return instance of FFI::Type"):
            space.execute("""
            class DataConverter
              def native_type; nil; end
              def to_native; nil; end
              def from_native; nil; end
            end
            FFI::Type::Mapped.new(DataConverter.new)
            """)

class TestFFI__Type__MappedObject_to_native(BaseFFITest):
    def test_it_delegates_to_the_data_converter(self, space):
        w_res = space.execute("""
        class DataConverter
          def native_type; FFI::Type::VOID; end
          def to_native; :success; end
          def from_native; nil; end
        end
        mapped = FFI::Type::Mapped.new(DataConverter.new)
        mapped.to_native
        """)
        assert self.unwrap(space, w_res) == 'success'

class TestFFI__Type__MappedObject_from_native(BaseFFITest):
    def test_it_delegates_from_the_data_converter(self, space):
        w_res = space.execute("""
        class DataConverter
          def native_type; FFI::Type::VOID; end
          def to_native; nil; end
          def from_native; :success; end
        end
        mapped = FFI::Type::Mapped.new(DataConverter.new)
        mapped.from_native
        """)
        assert self.unwrap(space, w_res) == 'success'

class TestFFI__Type_MappedObject(BaseFFITest):

    def test_it_converts_after_reading_and_writing(self, space):
        class RWStrategyMock(object):
            def read(self, space, data):
                return space.newsymbol(data)
            def write(self, space, data, w_obj):
                return data.append(space.str_w(w_obj))
        w_mapped = space.execute("""
        class DataConverter
          def native_type; FFI::Type::VOID; end
          def to_native(sym, _); sym.downcase; end
          def from_native(sym, _); sym.upcase; end
        end
        mapped = FFI::Type::Mapped.new(DataConverter.new)
        """)
        w_mapped.rw_strategy = RWStrategyMock()
        assert self.unwrap(space, w_mapped.read(space, "foo")) == "FOO"
        data = []
        w_mapped.write(space, data, space.newsymbol("BAR"))
        assert data == ["bar"]

