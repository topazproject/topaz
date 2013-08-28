from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.pointer import W_PointerObject

from rpython.rtyper.lltypesystem import rffi, lltype, llmemory

class TestPointer__NULL(BaseFFITest):
    def test_it_is_null(self, space):
        question = "FFI::Pointer::NULL.null?"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_it_is_instance_of_Pointer(self, space):
        question = "FFI::Pointer::NULL.class.equal? FFI::Pointer"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_it_eq_nil(self, space):
        question = "FFI::Pointer::NULL == nil"
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_it_raises_NullPointerError_on_read_write_methods(self, space):
        with self.raises(space, 'FFI::NullPointerError',
                         'read attempt on NULL pointer'):
            space.execute("FFI::Pointer::NULL.read_something")

class TestPointer__new(BaseFFITest):
    def test_it_returns_an_object_eq_to_NULL_when_given_0(self, space):
        assert self.ask(space, "FFI::Pointer.new(0) == FFI::Pointer::NULL")

    def test_it_serves_as_a_copy_constructor(self, space):
        assert self.ask(space, """
        FFI::Pointer.new(111) == FFI::Pointer.new(FFI::Pointer.new(111))
        """)

    def test_it_saves_a_pointer_to_whatever_address_was_given(self, space):
        char_ptr = lltype.malloc(rffi.CArray(rffi.CHAR), 1, flavor='raw')
        adr = llmemory.cast_ptr_to_adr(char_ptr)
        aint = llmemory.cast_adr_to_int(adr)
        ptr_obj = space.execute("""
        ptr = FFI::Pointer.new(%s)
        """ % aint)
        adr = llmemory.cast_ptr_to_adr(ptr_obj.ptr)
        assert llmemory.cast_adr_to_int(adr) == aint

    # TODO: This test doesn't work yet, because only addresses in uint range
    # are supported so far.
    #def test_it_also_accepts_negative_values(self, space):
    ## A negative value x is interpreted as 2**63 - x.
    #    for x in range(100):
    #        assert self.ask(space, """
    #        FFI::Pointer.new(X) == FFI::Pointer.new(2**63 - X)
    #        """.replace('X', str(x)))

    def test_it_can_also_be_called_with_a_type_size(self, space):
        char_ptr = lltype.malloc(rffi.CArray(rffi.SHORT), 1, flavor='raw')
        adr = llmemory.cast_ptr_to_adr(char_ptr)
        aint = llmemory.cast_adr_to_int(adr)
        ptr_obj = space.execute("""
        ptr = FFI::Pointer.new(2, %s)
        """ % aint)
        type_size = space.send(ptr_obj, 'type_size')
        assert self.unwrap(space, type_size) == 2
        adr = llmemory.cast_ptr_to_adr(ptr_obj.ptr)
        assert llmemory.cast_adr_to_int(adr) == aint

class TestPointer_size(BaseFFITest):
    def test_it_is_always_2_pow_63(self, space):
        for adr in range(100):
            w_res = space.execute("FFI::Pointer.new(%s).size" % adr)
            assert self.unwrap(space, w_res).toulonglong() == 2**63

class TestPointer_autorelease(BaseFFITest):
    def test_it(self, space):
        for question in ["FFI::Pointer.new(0).autorelease=(true)",
                         """
                         ptr = FFI::Pointer.new(0)
                         ptr.autorelease=(true)
                         ptr.autorelease?
                         """,
                         "not FFI::Pointer.new(0).autorelease=(false)",
                         """
                         ptr = FFI::Pointer.new(0)
                         ptr.autorelease=(false)
                         not ptr.autorelease?
                         """]:
            assert self.ask(space, question)

class TestPointer_address(BaseFFITest):
    def test_it_returns_the_address(self, space):
        w_res = space.execute("FFI::Pointer.new(42).address")
        assert self.unwrap(space, w_res) == 42

    def test_it_is_aliased_by_to_i(self, space):
        assert self.ask(space, """
        FFI::Pointer::instance_method(:to_i) ==
        FFI::Pointer::instance_method(:address)
        """)

class TestPointer_plus(BaseFFITest):
    def test_it_increases_the_address_by_the_2nd_arg(self, space):
        w_res = space.execute("(FFI::Pointer.new(3) + 2).address")
        assert self.unwrap(space, w_res) == 5

    def test_it_is_aliased_by_plus(self, space):
        assert self.ask(space, """
        FFI::Pointer.instance_method(:[]) ==
        FFI::Pointer.instance_method(:+)
        """)

class TestPointer_slice(BaseFFITest):
    def test_its_1st_arg_is_the_offset(self, space):
        w_res = space.execute("FFI::Pointer.new(14).slice(6, 0).address")
        assert self.unwrap(space, w_res) == 20

    def test_its_2nd_arg_is_the_size(self, space):
        w_res = space.execute("FFI::Pointer.new(3).slice(0, 4).size")
        assert self.unwrap(space, w_res) == 4

    def test_it_raises_TypeError_on_nonsense_args(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert String into Integer"):
            space.execute("FFI::Pointer.new(0).slice('15', 5)")
        with self.raises(space, 'TypeError',
                         "can't convert Symbol into Integer"):
            space.execute("FFI::Pointer.new(0).slice(0, :bar)")

class TestPointer(BaseFFITest):
    def test_its_superclass_is_AbstractMemory(self, space):
        assert self.ask(space,
        "FFI::Pointer.superclass.equal?(FFI::AbstractMemory)")

    def test_it_has_these_methods(self, space):
        # but they don't do anything yet...
        space.execute("FFI::Pointer.new(0).free")
        # order returns the endianess flag without argument
        # and sets the endianess flag if the 1st arg is valid
        # (meaning :big, :little, :network (which is also :big))
        # If the first arg is rubish it just returns self
        # Right now, it doesn't seen necessary to implement it.
        space.execute("FFI::Pointer.new(0).order(:big)")
        with self.raises(space, "TypeError", "42 is not a symbol"):
            space.execute("FFI::Pointer.new(0).order(42)")
