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
                   'double': 8}

    def test_total(self, space):
        for key in TestBuffer.sizes:
            w_res = space.execute("""
            buffer = FFI::Buffer.new(:%s, 3)
            buffer.total
            """ % key)
            expected = TestBuffer.sizes[key]*3
            assert self.unwrap(space, w_res) == expected

    def test_instantiations(self, space):
        generic_init = "FFI::Buffer.%s(:int, 5)"
        total_should = TestBuffer.sizes['int']*5
        for init_method in ['new',
                            'new_inout',
                            'new_in',
                            'new_out',
                            'alloc_inout',
                            'alloc_in',
                            'alloc_out']:
            w_buffer = space.execute(generic_init % init_method)
            w_buffer_total = space.send(w_buffer, 'total')
            assert total_should == self.unwrap(space, w_buffer_total)

    def test_default_size_is_1(self, space):
        w_res = space.execute("FFI::Buffer.alloc_in(7).total")
        assert self.unwrap(space, w_res) == 7

    def test_puts_return_self(self, space):
        for put in ['put_char',
                    'put_uchar',
                    'put_ushort',
                    'put_uint',
                    'put_ulong_long']:
            w_array = space.execute("""
            buffer = FFI::Buffer.new(:char, 8)
            put_result = buffer.%s(0, 0)
            [buffer, put_result]
            """ % put)
            w_buffers = w_array.listview(space)
            assert w_buffers[0] is w_buffers[1]

    def test_put_and_get_char(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 5)
        (0..4).each { |x| buffer.put_char(x, 127) }
        (0..4).map { |x| buffer.get_char(x) }
        """)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res) == 127 for w_res in w_chars])

    def test_put_and_get_uchar(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 5)
        (0..4).each { |x| buffer.put_uchar(x, 255) }
        (0..4).map { |x| buffer.get_uchar(x) }
        """)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res) == 255 for w_res in w_chars])

    def test_put_and_get_ushort(self, space):
        maxi = 256**2 - 1
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 6)
        (0..4).each { |x| buffer.put_ushort(x, %s) }
        (0..4).map { |x| buffer.get_ushort(x) }
        """ % maxi)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res) == maxi for w_res in w_chars])

    def test_put_and_get_uint(self, space):
        maxi = 256**4 - 1
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 8)
        (0..4).each { |x| buffer.put_uint(x, %s) }
        (0..4).map { |x| buffer.get_uint(x) }
        """ % maxi)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res) == maxi
                    for w_res in w_chars])

    def test_put_and_get_ulong_long(self, space):
        maxi = 256**8 - 1
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 12)
        (0..4).each { |x| buffer.put_ulong_long(x, %s) }
        (0..4).map { |x| buffer.get_ulong_long(x) }
        """  %  maxi)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res).tolong() == maxi
                    for w_res in w_chars])

    def test_put_returns_self(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.new(:char, 1)
        put_result = buffer.put_bytes(0, 'a')
        [buffer, put_result]
        """)
        w_buffers = w_array.listview(space)
        assert w_buffers[0] is w_buffers[1]

    def test_put_and_get_bytes(self, space):
        for i in range(2):
            w_res = space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 11)
            buffer.put_bytes(in_i, 'Hi there!')
            buffer.get_bytes(in_i, 9)
            """.replace('in_i', str(i)))
            assert self.unwrap(space, w_res) == 'Hi there!'
