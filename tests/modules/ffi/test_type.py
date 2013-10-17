from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.type import type_names, W_TypeObject, VOID

from rpython.rlib import clibffi

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

class TestFFI__TestType(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::NativeType.is_a? Module")

    def test_it_contains_some_type_constants(self, space):
        for typename in type_names:
            assert self.ask(space, "FFI::NativeType::%s.is_a? FFI::Type"
                            %typename)

    def test_it_has_these_instances_defined_as_constants(self, space):
        for typename in type_names:
            assert self.ask(space, "FFI::Type::%s.is_a? FFI::Type"
                            % typename)
            assert self.ask(space, "FFI::Type::%s.is_a? FFI::Type::Builtin"
                            % typename)

    def test_its_instances_can_be_accessed_in_different_ways(self, space):
        for typename in type_names:
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
