from tests.base import BaseTopazTest
from topaz.modules.ffi.buffer import W_BufferObject
from rpython.rtyper.lltypesystem.rffi import sizeof, LONG, ULONG

class TestBuffer(BaseTopazTest):

    sizes = {'char': 1,
                   'uchar': 1,
                   'short': 2,
                   'ushort': 2,
                   'int': 4,
                   'uint': 4,
                   'long': sizeof(LONG),
                   'ulong': sizeof(ULONG),
                   'long_long': 8,
                   'ulong_long': 8,
                   'float': 4,
                   'double': 8,
                   'pointer': 8}

    def test_total(self, space):
        for key in TestBuffer.sizes:
            w_res = space.execute("""
            buffer = FFI::Buffer.new(:%s, 3)
            buffer.total
            """ % key)
            expected = TestBuffer.sizes[key]*3
            assert self.unwrap(space, w_res) == expected

    def test_size_is_total(self, space):
        question = """
        buffer = FFI::Buffer.new(:char, 1)
        buffer.method(:total) == buffer.method(:size)
        """
        w_answer = space.execute(question)
        assert self.unwrap(space, w_answer)

    def test_non_valid_init_symbol(self, space):
        with self.raises(space, 'ArgumentError',
                         "I don't know the megaint type."):
            space.execute("FFI::Buffer.new(:megaint, 1)")

    def test_instantiations(self, space):
        question = "FFI::Buffer.method(:new) == FFI::Buffer.method(:%s)"
        for init_method in ['new_inout',
                            'new_in',
                            'new_out',
                            'alloc_inout',
                            'alloc_in',
                            'alloc_out']:
            w_answer = space.execute(question % init_method)
            assert self.unwrap(space, w_answer)

    def test_default_size_is_1(self, space):
        w_res = space.execute("FFI::Buffer.alloc_in(7).total")
        assert self.unwrap(space, w_res) == 7

    def test_default_length_is_1(self, space):
        w_res = space.execute("FFI::Buffer.alloc_in(:short).total")
        assert self.unwrap(space, w_res) == TestBuffer.sizes['short']

    def test_init_with_block(self, space):
        w_res = space.execute("""
        x = 0
        FFI::Buffer.new(:char, 5) { |len| x = len}
        x
        """)
        assert self.unwrap(space, w_res) == 5
        w_res = space.execute("""
        x = 0
        FFI::Buffer.new(3) { |len| x = len }
        x
        """)
        assert self.unwrap(space, w_res) == 3

    def test_puts_return_self(self, space):
        for put in ['put_char',
                    'put_uchar',
                    'put_short',
                    'put_ushort',
                    'put_int',
                    'put_uint',
                    'put_long_long',
                    'put_ulong_long']:
            w_buffers = space.execute("""
            buffer = FFI::Buffer.new(:char, 8)
            put_result = buffer.%s(0, 0)
            [buffer, put_result]
            """ % put)
            w_buffer, w_put_result = w_buffers.listview(space)
            assert w_buffer is w_put_result

    def test_put_and_get_char(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 3)
        buffer.put_char(0, -127)
        buffer.put_char(1, 0)
        buffer.put_char(2, 127)
        (0..2).map { |x| buffer.get_char(x) }
        """)
        res = self.unwrap(space, w_array)
        assert res == [-127, 0, 127]

    def test_call_put_char_in_wrong_situation(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert -128 into a char"):
            space.execute("""
            FFI::Buffer.alloc_in(:short, 1).put_char(0, -128)
            """)
        with self.raises(space, 'TypeError',
                         "can't convert 128 into a char"):
            space.execute("""
            FFI::Buffer.alloc_in(:short, 1).put_char(0, 128)
            """)

    def test_put_and_get_uchar(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:uchar, 3)
        buffer.put_uchar(0, 255)
        buffer.put_uchar(1, 127)
        buffer.put_uchar(2, 0)
        (0..2).map { |x| buffer.get_uchar(x) }
        """)
        res = self.unwrap(space, w_array)
        assert res == [255, 127, 0]

    def test_call_put_uchar_in_wrong_situation(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert -1 into a uchar"):
            space.execute("""
            FFI::Buffer.alloc_in(:char, 1).put_uchar(0, -1)
            """)
        with self.raises(space, 'TypeError',
                         "can't convert 256 into a uchar"):
            space.execute("""
            FFI::Buffer.alloc_in(:short, 1).put_uchar(0, 256)
            """)

    def test_put_and_get_short(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:short, 3)
        buffer.put_short(0, -(2**15 - 1))
        buffer.put_short(2, 2**15 - 1)
        buffer.put_short(4, 0)
        [0, 2, 4].map { |x| buffer.get_short(x) }
        """)
        res = self.unwrap(space, w_array)
        assert res == [-(2**15 - 1), 2**15 - 1, 0]

    def test_call_put_short_in_wrong_situation(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert -32768 into a short"):
            space.execute("""
            FFI::Buffer.alloc_in(:int, 1).put_short(0, - 2**15)
            """)
        with self.raises(space, 'TypeError',
                         "can't convert 32768 into a short"):
            space.execute("""
            FFI::Buffer.alloc_in(:int, 1).put_short(0, 2**15)
            """)

    def test_put_and_get_ushort(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:ushort, 3)
        buffer.put_ushort(0, 256**2 - 1)
        buffer.put_ushort(2, 256)
        buffer.put_ushort(4, 0)
        [0, 2, 4].map { |x| buffer.get_ushort(x) }
        """)
        res = self.unwrap(space, w_array)
        assert res == [256**2 - 1, 256, 0]

    def test_call_put_ushort_in_wrong_situation(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert -1 into a ushort"):
            space.execute("""
            FFI::Buffer.alloc_in(:char, 1).put_ushort(0, -1)
            """)
        with self.raises(space, 'TypeError',
                         "can't convert 65536 into a ushort"):
            space.execute("""
            FFI::Buffer.alloc_in(:int, 1).put_ushort(0, 2**16)
            """)

    def test_put_and_get_int(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:int, 3)
        buffer.put_int(0, -(2**31 - 1))
        buffer.put_int(4, 2**31 - 1)
        buffer.put_int(8, 0)
        [0, 4, 8].map { |x| buffer.get_int(x) }
        """)
        res = self.unwrap(space, w_array)
        assert res == [-(2**31 - 1), 2**31 - 1, 0]

    def test_call_put_int_in_wrong_situation(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert -2147483648 into an int"):
            space.execute("""
            FFI::Buffer.alloc_in(:long_long, 1).put_int(0, - 2**31)
            """)
        with self.raises(space, 'TypeError',
                         "can't convert 2147483648 into an int"):
            space.execute("""
            FFI::Buffer.alloc_in(:long_long, 1).put_int(0, 2**31)
            """)

    def test_put_and_get_uint(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:uint, 3)
        buffer.put_uint(0, 256**4 - 1)
        buffer.put_uint(4, 2222222222)
        buffer.put_uint(8, 0)
        [0, 4, 8].map { |x| buffer.get_uint(x) }
        """)
        res = self.unwrap(space, w_array)
        assert res == [256**4 - 1, 2222222222, 0]

    def test_call_put_uint_in_wrong_situation(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert -1 into a uint"):
            space.execute("""
            FFI::Buffer.alloc_in(:char, 1).put_uint(0, -1)
            """)
        with self.raises(space, 'TypeError',
                         "can't convert 4294967296 into a uint"):
            space.execute("""
            FFI::Buffer.alloc_in(:long_long, 1).put_uint(0, 2**32)
            """)

    def test_put_and_get_long_long(self, space):
        w_res = space.execute("""
        buffer = FFI::Buffer.alloc_in(:long_long, 3)
        buffer.put_long_long(0, - 2**62)
        buffer.put_long_long(8, 2**62)
        buffer.put_long_long(16, 0)
        [0, 8, 16].map { |x| buffer.get_long_long(x) }
        """)
        res = [i.toint() for i in self.unwrap(space, w_res)]
        assert res == [- 2**62, 2**62, 0]

    # test_call_put_long_long_in_wrong_situation delayed until
    # 2**63 works in topaz.
    def test_call_put_long_long_in_wrong_situation(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert -9223372036854775808 into a long long"):
            space.execute("""
            FFI::Buffer.alloc_in(:long_long, 1).put_long_long(0, - 2**63)
            """)
        with self.raises(space, 'TypeError',
                         "can't convert 9223372036854775808 into a long long"):
            space.execute("""
            FFI::Buffer.alloc_in(:long_long, 1).put_long_long(0, 2**63)
            """)

    def test_put_and_get_ulong_long(self, space):
        w_res = space.execute("""
        buffer = FFI::Buffer.alloc_in(:ulong_long, 3)
        buffer.put_ulong_long(0, 2**62)
        buffer.put_ulong_long(8, 256**4 + 5)
        buffer.put_ulong_long(16, 0)
        [0, 8, 16].map { |x| buffer.get_ulong_long(x) }
        """)
        res = [l.tolong() for l in self.unwrap(space, w_res)]
        assert res == [2**62, 256**4 + 5, 0]

    def test_call_put_ulong_long_in_wrong_situation(self, space):
        with self.raises(space, 'TypeError',
                         "can't convert -1 into a ulong_long"):
            space.execute("""
            FFI::Buffer.alloc_in(:char, 1).put_ulong_long(0, -1)
            """)
        with self.raises(space, 'TypeError',
                         "can't convert 18446744073709551616 into a ulong_long"):
            space.execute("""
            FFI::Buffer.alloc_in(:long_long, 1).put_ulong_long(0, 2**64)
            """)

    def test_put_bytes_returns_self(self, space):
        w_buffers = space.execute("""
        buffer = FFI::Buffer.new(:char, 1)
        put_result = buffer.put_bytes(0, 'a')
        [buffer, put_result]
        """)
        w_buffer, w_put_result = w_buffers.listview(space)
        assert w_buffer is w_put_result

    def test_put_and_get_bytes(self, space):
        for i in range(2):
            w_res = space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 11)
            buffer.put_bytes(in_i, 'Hi there!')
            buffer.get_bytes(in_i, 9)
            """.replace('in_i', str(i)))
            assert self.unwrap(space, w_res) == 'Hi there!'

    def test_put_bytes_index_and_length(self, space):
        w_res = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 3)
        buffer.put_bytes(0, '0123456', 2, 3)
        buffer.get_bytes(0, 3)
        """)
        assert self.unwrap(space, w_res) == '234'

    def test_put_bytes_too_big_index_error(self, space):
        with self.raises(space, 'IndexError',
                         "Tried to start at index 3 of str 012"):
            space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 3)
            buffer.put_bytes(0, '012', 3)
            """)

    def test_put_bytes_negative_index_error(self, space):
        with self.raises(space, 'IndexError',
                         "Tried to start at index -1 of str 012"):
            space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 3)
            buffer.put_bytes(0, '012', -1)
            """)

    def test_put_bytes_length_error(self, space):
        with self.raises(space, 'IndexError',
                         "Tried to end at index 5 of str 0123"):
            space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 3)
            buffer.put_bytes(0, '0123', 1, 4)
            """)

    def test_write_bytes_is_put_bytes_with_offset_eq_0(self, space):
        w_res = space.execute("""
        buffer = FFI::Buffer.new(:char, 3)
        buffer.write_bytes('foo')
        buffer.get_bytes(0, 3)
        """)
        assert self.unwrap(space, w_res) == 'foo'

    # TODO: Put everything into the space.execute section
    #       once the lexer can handle \0.
    def test_get_string(self, space):
        w_buffer = space.execute("""
        FFI::Buffer.alloc_in(:char, 11)
        """)
        space.send(w_buffer, 'put_bytes',
                   [space.newint(0), space.newstr_fromstr('Hi\0there')])
        w_res = space.send(w_buffer, 'get_string',
                           [space.newint(0), space.newint(9)])
        assert self.unwrap(space, w_res) == 'Hi'
