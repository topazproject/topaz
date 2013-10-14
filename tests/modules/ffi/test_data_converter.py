import pytest
from tests.modules.ffi.base import BaseFFITest

class TestDataConverter(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::DataConverter.is_a? Module")

    def test_it_has_the_following_instance_methods(self, space):
        w_res = space.execute("FFI::DataConverter.instance_methods")
        instance_methods = self.unwrap(space, w_res)
        assert 'native_type' in instance_methods
        assert 'to_native' in instance_methods
        assert 'from_native' in instance_methods

code_DataConverterImplementation = """
class DataConverterImplementation
  include FFI::DataConverter

  def impl_native_type(*args)
    native_type(*args)
  end

  def impl_from_native(*args)
    from_native(*args)
  end

  def impl_to_native(*args)
    to_native(*args)
  end
end
"""

class TestDataConverter__native_type(BaseFFITest):

    @pytest.mark.xfail
    def test_it_raises_NotImplementedError_without_args(self, space):
        space.execute(code_DataConverterImplementation)
        with self.raises(space, "NotImplementedError",
                                "native_type method not overridden and no "
                                "native_type set"):
            space.execute("""
            DataConverterImplementation.new.impl_native_type
            """)


    def test_it_calls_find_type_if_one_arg_was_given(self, space):
        space.execute(code_DataConverterImplementation)
        w_res = space.execute("""
        def FFI.find_type(arg)
          return arg
        end
        DataConverterImplementation.new.impl_native_type(FFI::Type::VOID)
        """)
        assert w_res is space.execute("FFI::Type::VOID")

    def test_it_returns_the_result_of_find_type(self, ffis):
        ffis.execute(code_DataConverterImplementation)
        self.ask(ffis, """
        DataConverterImplementation.new.impl_native_type(:void).equal? FFI::Type::VOID
        """)

    def test_it_sets_the_result_of_find_type_as_attr(self, ffis):
        ffis.execute(code_DataConverterImplementation)
        w_res = ffis.execute("""
        dci = DataConverterImplementation.new
        dci.impl_native_type(:void)
        class DataConverterImplementation
          attr_reader :native_type
        end
        dci.native_type
        """)
        assert w_res is ffis.execute("FFI::Type::VOID")

    def test_it_raises_ArgumentError_for_more_than_1_arg(self, space):
        space.execute(code_DataConverterImplementation)
        with self.raises(space, "ArgumentError", "incorrect arguments"):
            space.execute("""
            DataConverterImplementation.new.impl_native_type(:int8, :more)
            """)

def check_it_takes_two_args_and_returns_the_first(ffitest, space, funcname):
    space.execute(code_DataConverterImplementation)
    w_res = space.execute("%s(1, 2)" %funcname)
    assert ffitest.unwrap(space, w_res) == 1
    with ffitest.raises(space, "ArgumentError"):
        space.execute(funcname)
    with ffitest.raises(space, "ArgumentError"):
        space.execute("%s(1)" %funcname)
    with ffitest.raises(space, "ArgumentError"):
        space.execute("%s(1, 2, 3)" %funcname)

class TestDataConverter__to_native(BaseFFITest):
    def test_it_takes_two_arguments_and_returns_the_first_one(self, space):
        check_it_takes_two_args_and_returns_the_first(self, space,
                                                      "DataConverterImplementation.new.impl_to_native")

class TestDataConverter__from_native(BaseFFITest):
    def test_it_returns_nil_for_now(self, space):
        check_it_takes_two_args_and_returns_the_first(self, space,
                                                      "DataConverterImplementation.new.impl_from_native")
