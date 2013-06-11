from tests.base import BaseTopazTest
from topaz.objects.classobject import W_ClassObject

class TestFunction(BaseTopazTest):

    def test_initialize(self, space):
        w_function = space.execute("""
        FFI::Function.new(:void, [:int8, :int16], :funcname, {})
        """) #didn't crash
        w_function = space.execute("""
        FFI::Function.new(FFI::Type::VOID,
                          [FFI::Type::INT8, FFI::Type::INT16], :fname, {})
        """) # didn't crash
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(1, [], :fname, {})")
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(:void, [2], :fname, {})")
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:null, [], :fname, {})")
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:int32, [:array], :fname, {})")
