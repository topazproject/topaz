from tests.base import BaseTopazTest
from topaz.objects.classobject import W_ClassObject

class TestFunction(BaseTopazTest):

    def test_initialize(self, space):
        w_function = space.execute("""
        FFI::Function.new(:void, [:int8, :int16], {})
        """) #didn't crash
        w_function = space.execute("""
        FFI::Function.new(FFI::Type::VOID,
                          [FFI::Type::INT8, FFI::Type::INT16], {})
        """) # didn't crash
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(1, [], {})")
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:null, [], {})")
