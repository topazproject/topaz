import sys

from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.pointer import coerce_address

from rpython.rtyper.lltypesystem import rffi, lltype, llmemory
from rpython.rtyper.lltypesystem.ll2ctypes import ALLOCATED

class TestPointer__NULL(BaseFFITest):
    def test_it_is_null(self, space):
        self.ask(space, "FFI::Pointer::NULL.null?")

    def test_it_is_instance_of_Pointer(self, space):
        self.ask(space, "FFI::Pointer::NULL.class.equal? FFI::Pointer")

    def test_it_eq_nil(self, space):
        self.ask(space, "FFI::Pointer::NULL == nil")

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
        int8_ptr = lltype.malloc(rffi.CArray(rffi.CHAR), 1, flavor='raw')
        adr = llmemory.cast_ptr_to_adr(int8_ptr)
        aint = llmemory.cast_adr_to_int(adr, mode='forced')
        w_ptr_obj = space.execute("""
        ptr = FFI::Pointer.new(%s)
        """ % aint)
        adr = llmemory.cast_ptr_to_adr(w_ptr_obj.ptr)
        assert llmemory.cast_adr_to_int(adr, mode='forced') == aint
        lltype.free(int8_ptr, flavor='raw')
        assert not aint in ALLOCATED

    def test_it_also_accepts_negative_values(self, space):
        for x in range(1, 100):
            assert self.ask(space, """
            FFI::Pointer.new(-{X}) != 0
            """.format(X=str(x)))

    def test_it_can_also_be_called_with_a_type_size(self, space):
        int16_ptr = lltype.malloc(rffi.CArray(rffi.SHORT), 1, flavor='raw')
        adr = llmemory.cast_ptr_to_adr(int16_ptr)
        aint = llmemory.cast_adr_to_int(adr, mode='forced')
        # be careful: the first argument is the type size and the second the
        #             address, not vice versa
        ptr_obj = space.execute("""
        ptr = FFI::Pointer.new(2, %s)
        """ % aint)
        type_size = space.send(ptr_obj, 'type_size')
        assert self.unwrap(space, type_size) == 2
        adr = llmemory.cast_ptr_to_adr(ptr_obj.ptr)
        assert llmemory.cast_adr_to_int(adr, mode='forced') == aint
        lltype.free(int16_ptr, flavor='raw')
        assert not aint in ALLOCATED

class TestPointer_size(BaseFFITest):
    def test_it_is_always_2_pow_63(self, space):
        for adr in range(100):
            w_res = space.execute("FFI::Pointer.new(%s).size" % adr)
            assert self.unwrap(space, w_res) == sys.maxint

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

class TestPointer_free(BaseFFITest):
    def test_it_frees_whatever_the_Pointer_is_referencing(self, space):
        int16_ptr = lltype.malloc(rffi.CArray(rffi.SHORT), 1, flavor='raw')
        adr = llmemory.cast_ptr_to_adr(int16_ptr)
        aint = llmemory.cast_adr_to_int(adr, mode='forced')
        space.execute("FFI::Pointer.new(%s).free" % aint)
        assert not aint in ALLOCATED

class TestPointer(BaseFFITest):
    def test_its_superclass_is_AbstractMemory(self, space):
        assert self.ask(space,
        "FFI::Pointer.superclass.equal?(FFI::AbstractMemory)")

    def test_it_has_these_methods(self, space):
        # but they don't do anything yet...
        # order returns the endianess flag without argument
        # and sets the endianess flag if the 1st arg is valid
        # (meaning :big, :little, :network (which is also :big))
        # If the first arg is rubish it just returns self
        # Right now, it doesn't seen necessary to implement it.
        space.execute("FFI::Pointer.new(0).order(:big)")
        with self.raises(space, "TypeError", "42 is not a symbol"):
            space.execute("FFI::Pointer.new(0).order(42)")

class Test_coerce_address(BaseFFITest):
    def test_it_accepts_ruby_Fixnum_as_address(self, space):
        assert coerce_address(space, space.newint(2)) == 2

    def test_it_accepts_ruby_Bignum_as_address(self, space):
        assert coerce_address(space, space.newbigint_fromint(1)) == 1

    def test_it_accepts_FFI__Pointer_as_address(self, space):
        w_ptr = space.execute("FFI::Pointer.new(6)")
        assert coerce_address(space, w_ptr) == 6

    def test_it_raises_ruby_TypeError_on_anything_else(self, space):
        with self.raises(space, "TypeError",
                         "can't convert Symbol into FFI::Pointer"):
            coerce_address(space, space.newsymbol('error'))
