from tests.modules.ffi.base import BaseFFITest

class TestDataConverter(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::DataConverter.is_a? Module")

class TestDataConverter__native_type(BaseFFITest):
    def test_it_raises_NotImplementedError_without_args(self, space):
        with self.raises(space, "NotImplementedError",
                                "native_type method not overridden and no"
                                "native_type set"):
            space.execute("FFI::DataConverter.native_type")

    code_data_converter_test = """
    class DataConverterTest
      include FFI::DataConverter

      def run(*args)
        native_type(*args)
      end
    end
    data_converter_test = DataConverterTest.new
    """

    def test_it_calls_find_type_if_one_arg_was_given(self, space):
        w_res = space.execute("""
        %s
        def FFI.find_type(arg)
          return arg
        end
        data_converter_test.run(FFI::Type::VOID)
        """ % self.code_data_converter_test)
        assert w_res is space.execute("FFI::Type::VOID")

    def test_it_returns_the_result_of_find_type(self, ffis):
        self.ask(ffis, """
        %s
        data_converter_test.run(:void).equal? FFI::Type::VOID
        """ % self.code_data_converter_test)

    def test_it_sets_the_result_of_find_type_as_attr(self, ffis):
        w_res = ffis.execute("""
        %s
        data_converter_test.run(:void)
        class DataConverterTest
          attr_reader :native_type
        end
        data_converter_test.native_type
        """ % self.code_data_converter_test)
        assert w_res is ffis.execute("FFI::Type::VOID")

    def test_it_raises_ArgumentError_for_more_than_1_arg(self, space):
        with self.raises(space, "ArgumentError", "incorrect arguments"):
            space.execute("""
            %s
            data_converter_test.run(:int8, :more)
            """ % self.code_data_converter_test)

def check_it_takes_two_args_and_returns_the_first(ffitest, space, funcname):
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
                                                      "FFI::DataConverter.to_native")

class TestDataConverter__from_native(BaseFFITest):
    def test_it_returns_nil_for_now(self, space):
        check_it_takes_two_args_and_returns_the_first(self, space,
                                                      "FFI::DataConverter.from_native")
