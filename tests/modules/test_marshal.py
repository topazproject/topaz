from ..base import BaseTopazTest


class TestMarshal(BaseTopazTest):
    def test_version_constants(self, space):
        w_res = space.execute("return Marshal::MAJOR_VERSION")
        assert space.int_w(w_res) == 4

        w_res = space.execute("return Marshal::MINOR_VERSION")
        assert space.int_w(w_res) == 8

        w_res = space.execute("return Marshal.dump('test')[0].ord")
        assert space.int_w(w_res) == 4

        w_res = space.execute("return Marshal.dump('test')[1].ord")
        assert space.int_w(w_res) == 8

    def test_dump_constants(self, space):
        w_res = space.execute("return Marshal.dump(nil)")
        assert space.str_w(w_res) == "\x04\b0"

        w_res = space.execute("return Marshal.dump(true)")
        assert space.str_w(w_res) == "\x04\bT"

        w_res = space.execute("return Marshal.dump(false)")
        assert space.str_w(w_res) == "\x04\bF"

    def test_load_constants(self, space):
        w_res = space.execute("return Marshal.load('\x04\b0')")
        assert w_res == space.w_nil

        w_res = space.execute("return Marshal.load('\x04\bT')")
        assert w_res == space.w_true

        w_res = space.execute("return Marshal.load('\x04\bF')")
        assert w_res == space.w_false

    def test_constants(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump(nil))")
        assert w_res == space.w_nil

        w_res = space.execute("return Marshal.load(Marshal.dump(true))")
        assert w_res == space.w_true

        w_res = space.execute("return Marshal.load(Marshal.dump(false))")
        assert w_res == space.w_false

    def test_dump_tiny_integer(self, space):
        w_res = space.execute("return Marshal.dump(5)")
        assert space.str_w(w_res) == "\x04\bi\n"

        w_res = space.execute("return Marshal.dump(100)")
        assert space.str_w(w_res) == "\x04\bii"

        w_res = space.execute("return Marshal.dump(0)")
        assert space.str_w(w_res) == "\x04\bi\x00"

        w_res = space.execute("return Marshal.dump(-1)")
        assert space.str_w(w_res) == "\x04\bi\xFA"

        w_res = space.execute("return Marshal.dump(-123)")
        assert space.str_w(w_res) == "\x04\bi\x80"

        w_res = space.execute("return Marshal.dump(122)")
        assert space.str_w(w_res) == "\x04\bi\x7F"

    def test_load_tiny_integer(self, space):
        w_res = space.execute("return Marshal.load('\x04\bi\n')")
        assert space.int_w(w_res) == 5

        w_res = space.execute("return Marshal.load('\x04\bii')")
        assert space.int_w(w_res) == 100

        #w_res = space.execute('return Marshal.load("\x04\bi\x00")')
        w_res = space.execute('return Marshal.load(Marshal.dump(0))')
        assert space.int_w(w_res) == 0

        w_res = space.execute("return Marshal.load('\x04\bi\xFA')")
        assert space.int_w(w_res) == -1

        w_res = space.execute("return Marshal.load('\x04\bi\x80')")
        assert space.int_w(w_res) == -123

        w_res = space.execute("return Marshal.load('\x04\bi\x7F')")
        assert space.int_w(w_res) == 122

    def test_dump_array(self, space):
        w_res = space.execute("return Marshal.dump([])")
        assert space.str_w(w_res) == "\x04\b[\x00"

        w_res = space.execute("return Marshal.dump([nil])")
        assert space.str_w(w_res) == "\x04\b[\x060"

        w_res = space.execute("return Marshal.dump([nil, true, false])")
        assert space.str_w(w_res) == "\x04\b[\b0TF"

        w_res = space.execute("return Marshal.dump([1, 2, 3])")
        assert space.str_w(w_res) == "\x04\b[\x08i\x06i\x07i\x08"

        w_res = space.execute("return Marshal.dump([1, [2, 3], 4])")
        assert space.str_w(w_res) == "\x04\b[\bi\x06[\ai\ai\bi\t"

        w_res = space.execute("return Marshal.dump([:foo, :bar])")
        assert space.str_w(w_res) == "\x04\b[\a:\bfoo:\bbar"

    def test_load_array(self, space):
        #w_res = space.execute("return Marshal.load('\x04\b[\x00')")
        w_res = space.execute("return Marshal.load(Marshal.dump([]))")
        assert self.unwrap(space, w_res) == []

        w_res = space.execute("return Marshal.load('\x04\b[\x060')")
        assert self.unwrap(space, w_res) == [None]

        w_res = space.execute("return Marshal.load('\x04\b[\b0TF')")
        assert self.unwrap(space, w_res) == [None, True, False]

        w_res = space.execute("return Marshal.load('\x04\b[\x08i\x06i\x07i\x08')")
        assert self.unwrap(space, w_res) == [1, 2, 3]

        w_res = space.execute("return Marshal.load('\x04\b[\bi\x06[\ai\ai\bi\t')")
        assert self.unwrap(space, w_res) == [1, [2, 3], 4]

        w_res = space.execute("return Marshal.load('\x04\b[\a:\bfoo:\bbar')")
        assert self.unwrap(space, w_res) == ["foo", "bar"]

    def test_dump_symbol(self, space):
        w_res = space.execute("return Marshal.dump(:abc)")
        assert space.str_w(w_res) == "\x04\b:\babc"

        w_res = space.execute("return Marshal.dump(('hello' * 25).to_sym)")
        assert space.str_w(w_res) == "\x04\b:\x01}" + "hello" * 25

        w_res = space.execute("return Marshal.dump(('hello' * 100).to_sym)")
        assert space.str_w(w_res) == "\x04\b:\x02\xF4\x01" + "hello" * 100

    def test_load_symbol(self, space):
        w_res = space.execute("return Marshal.load('\x04\b:\babc')")
        assert space.symbol_w(w_res) == "abc"

        w_res = space.execute("return Marshal.load('\x04\b:\x01}' + 'hello' * 25)")
        assert space.symbol_w(w_res) == "hello" * 25

    def test_dump_hash(self, space):
        w_res = space.execute("return Marshal.dump({})")
        assert space.str_w(w_res) == "\x04\b{\x00"

        w_res = space.execute("return Marshal.dump({1 => 2, 3 => 4})")
        assert self.unwrap(space, w_res) == "\x04\b{\ai\x06i\ai\bi\t"

        w_res = space.execute("return Marshal.dump({1 => {2 => 3}, 4 => 5})")
        assert self.unwrap(space, w_res) == "\x04\b{\ai\x06{\x06i\ai\bi\ti\n"

        w_res = space.execute("return Marshal.dump({1234 => {23456 => 3456789}, 4 => 5})")
        assert self.unwrap(space, w_res) == "\x04\b{\ai\x02\xD2\x04{\x06i\x02\xA0[i\x03\x15\xBF4i\ti\n"

    def test_load_hash(self, space):
        #w_res = space.execute("return Marshal.load('\x04\b{\x00')")
        w_res = space.execute("return Marshal.load(Marshal.dump({}))")
        assert self.unwrap(space, w_res) == {}

        w_res = space.execute("return Marshal.load('\x04\b{\ai\x06i\ai\bi\t')")
        assert self.unwrap(space, w_res) == {1: 2, 3: 4}

        w_res = space.execute("return Marshal.load('\x04\b{\ai\x06{\x06i\ai\bi\ti\n')")
        assert self.unwrap(space, w_res) == {1: {2: 3}, 4: 5}

        w_res = space.execute("return Marshal.load('\x04\b{\ai\x02\xD2\x04{\x06i\x02\xA0[i\x03\x15\xBF4i\ti\n')")
        assert self.unwrap(space, w_res) == {1234: {23456: 3456789}, 4: 5}

    def test_dump_integer(self, space):
        w_res = space.execute("return Marshal.dump(123)")
        assert space.str_w(w_res) == "\x04\bi\x01{"

        w_res = space.execute("return Marshal.dump(255)")
        assert space.str_w(w_res) == "\x04\bi\x01\xFF"

        w_res = space.execute("return Marshal.dump(256)")
        assert space.str_w(w_res) == "\x04\bi\x02\x00\x01"

        w_res = space.execute("return Marshal.dump(2 ** 16 - 2)")
        assert space.str_w(w_res) == "\x04\bi\x02\xFE\xFF"

        w_res = space.execute("return Marshal.dump(2 ** 16 - 1)")
        assert space.str_w(w_res) == "\x04\bi\x02\xFF\xFF"

        w_res = space.execute("return Marshal.dump(2 ** 16)")
        assert space.str_w(w_res) == "\x04\bi\x03\x00\x00\x01"

        w_res = space.execute("return Marshal.dump(2 ** 16 + 1)")
        assert space.str_w(w_res) == "\x04\bi\x03\x01\x00\x01"

        w_res = space.execute("return Marshal.dump(2 ** 30 - 1)")
        assert space.str_w(w_res) == "\x04\bi\x04\xFF\xFF\xFF?"

        # TODO: test tooo big numbers (they give a warning and inf)

    def test_load_integer(self, space):
        w_res = space.execute("return Marshal.load('\x04\bi\x01{')")
        assert space.int_w(w_res) == 123

        w_res = space.execute("return Marshal.load('\x04\bi\x01\xFF')")
        assert space.int_w(w_res) == 255

        #w_res = space.execute("return Marshal.load('\x04\bi\x02\x00\x01')")
        w_res = space.execute("return Marshal.load(Marshal.dump(256))")
        assert space.int_w(w_res) == 256

        w_res = space.execute("return Marshal.load('\x04\bi\x02\xFE\xFF')")
        assert space.int_w(w_res) == 2 ** 16 - 2

        w_res = space.execute("return Marshal.load('\x04\bi\x02\xFF\xFF')")
        assert space.int_w(w_res) == 2 ** 16 - 1

        #w_res = space.execute("return Marshal.load('\x04\bi\x03\x00\x00\x01')")
        w_res = space.execute("return Marshal.load(Marshal.dump(2 ** 16))")
        assert space.int_w(w_res) == 2 ** 16

        #w_res = space.execute("return Marshal.load('\x04\bi\x03\x01\x00\x01')")
        w_res = space.execute("return Marshal.load(Marshal.dump(2 ** 16 + 1))")
        assert space.int_w(w_res) == 2 ** 16 + 1

        w_res = space.execute("return Marshal.load('\x04\bi\x04\xFF\xFF\xFF?')")
        assert space.int_w(w_res) == 2 ** 30 - 1

    def test_dump_negative_integer(self, space):
        w_res = space.execute("return Marshal.dump(-1)")
        assert space.str_w(w_res) == "\x04\bi\xFA"

        w_res = space.execute("return Marshal.dump(-123)")
        assert space.str_w(w_res) == "\x04\bi\x80"

        w_res = space.execute("return Marshal.dump(-124)")
        assert space.str_w(w_res) == "\x04\bi\xFF\x84"

        w_res = space.execute("return Marshal.dump(-256)")
        assert space.str_w(w_res) == "\x04\bi\xFF\x00"

        w_res = space.execute("return Marshal.dump(-257)")
        assert space.str_w(w_res) == "\x04\bi\xFE\xFF\xFE"

        w_res = space.execute("return Marshal.dump(-(2 ** 30))")
        assert space.str_w(w_res) == "\x04\bi\xFC\x00\x00\x00\xC0"

    def test_load_negative_integer(self, space):
        w_res = space.execute("return Marshal.load('\x04\bi\xFA')")
        assert space.int_w(w_res) == -1

        w_res = space.execute("return Marshal.load('\x04\bi\x80')")
        assert space.int_w(w_res) == -123

        w_res = space.execute("return Marshal.load('\x04\bi\xFF\x84')")
        assert space.int_w(w_res) == -124

        #w_res = space.execute("return Marshal.load('\x04\bi\xFF\x00')")
        w_res = space.execute("return Marshal.load(Marshal.dump(-256))")
        assert space.int_w(w_res) == -256

        w_res = space.execute("return Marshal.load('\x04\bi\xFE\xFF\xFE')")
        assert space.int_w(w_res) == -257

        #w_res = space.execute("return Marshal.load('\x04\bi\xFE\x00\x00')")
        w_res = space.execute("return Marshal.load(Marshal.dump(-(2 ** 16)))")
        assert space.int_w(w_res) == -(2 ** 16)

        w_res = space.execute("return Marshal.load('\x04\bi\xFD\xFF\xFF\xFE')")
        assert space.int_w(w_res) == -(2 ** 16 + 1)

        #w_res = space.execute("return Marshal.load('\x04\bi\xFC\x00\x00\x00')")
        w_res = space.execute("return Marshal.load(Marshal.dump(-(2 ** 24)))")
        assert space.int_w(w_res) == -(2 ** 24)

        w_res = space.execute("return Marshal.load('\x04\bi\xFC\xFF\xFF\xFF\xFE')")
        assert space.int_w(w_res) == -(2 ** 24 + 1)

        #w_res = space.execute("return Marshal.load('\x04\bi\xFC\x00\x00\x00\xC0')")
        w_res = space.execute("return Marshal.load(Marshal.dump(-(2 ** 30)))")
        assert space.int_w(w_res) == -(2 ** 30)

    def test_dump_float(self, space):
        w_res = space.execute("return Marshal.dump(0.0)")
        assert space.str_w(w_res) == "\x04\bf\x060"

        w_res = space.execute("return Marshal.dump(0.1)")
        assert space.str_w(w_res) == "\x04\bf\b0.1"

        w_res = space.execute("return Marshal.dump(1.0)")
        assert space.str_w(w_res) == "\x04\bf\x061"

        w_res = space.execute("return Marshal.dump(1.1)")
        assert space.str_w(w_res) == "\x04\bf\b1.1"

        w_res = space.execute("return Marshal.dump(1.001)")
        assert space.str_w(w_res) == "\x04\bf\n1.001"

        #w_res = space.execute("return Marshal.dump(123456789.123456789)")
        #assert space.str_w(w_res) == "\x04\bf\x17123456789.12345679"

        #w_res = space.execute("return Marshal.dump(-123456789.123456789)")
        #assert space.str_w(w_res) == "\x04\bf\x18-123456789.12345679"

        #w_res = space.execute("return Marshal.dump(-0.0)")
        #assert space.str_w(w_res) == "\x04\bf\a-0"

    def test_load_float(self, space):
        w_res = space.execute("return Marshal.load('\x04\bf\x060')")
        assert space.float_w(w_res) == 0.0

        w_res = space.execute("return Marshal.load('\x04\bf\b0.1')")
        assert space.float_w(w_res) == 0.1

        w_res = space.execute("return Marshal.load('\x04\bf\x061')")
        assert space.float_w(w_res) == 1.0

        w_res = space.execute("return Marshal.load('\x04\bf\b1.1')")
        assert space.float_w(w_res) == 1.1

        w_res = space.execute("return Marshal.load('\x04\bf\n1.001')")
        assert space.float_w(w_res) == 1.001

        #w_res = space.execute("return Marshal.load('\x04\bf\x17123456789.12345679')")
        #assert space.float_w(w_res) == 123456789.123456789

        #w_res = space.execute("return Marshal.load('\x04\bf\x18-123456789.12345679')")
        #assert space.float_w(w_res) == -123456789.123456789

        #w_res = space.execute("return Marshal.load('\x04\bf\a-0')")
        #assert repr(space.float_w(w_res)) == repr(-0.0)

    def test_dump_string(self, space):
        w_res = space.execute("return Marshal.dump('')")
        assert space.str_w(w_res) == "\x04\bI\"\x00\x06:\x06ET"

        w_res = space.execute("return Marshal.dump('abc')")
        assert space.str_w(w_res) == "\x04\bI\"\babc\x06:\x06ET"

        w_res = space.execute("return Marshal.dump('i am a longer string')")
        assert space.str_w(w_res) == "\x04\bI\"\x19i am a longer string\x06:\x06ET"

    def test_load_string(self, space):
        #w_res = space.execute("return Marshal.load('\x04\bI\"\x00\x06:\x06ET')")
        w_res = space.execute("return Marshal.load(Marshal.dump(''))")
        assert space.str_w(w_res) == ""

        w_res = space.execute("return Marshal.load('\x04\bI\"\babc\x06:\x06ET')")
        assert space.str_w(w_res) == "abc"

        w_res = space.execute("return Marshal.load('\x04\bI\"\x19i am a longer string\x06:\x06ET')")
        assert space.str_w(w_res) == "i am a longer string"

    def test_array(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump([1, 2, 3]))")
        assert self.unwrap(space, w_res) == [1, 2, 3]

        w_res = space.execute("return Marshal.load(Marshal.dump([1, [2, 3], 4]))")
        assert self.unwrap(space, w_res) == [1, [2, 3], 4]

        w_res = space.execute("return Marshal.load(Marshal.dump([130, [2, 3], 4]))")
        assert self.unwrap(space, w_res) == [130, [2, 3], 4]

        w_res = space.execute("return Marshal.load(Marshal.dump([-10000, [2, 123456], -9000]))")
        assert self.unwrap(space, w_res) == [-10000, [2, 123456], -9000]

        w_res = space.execute("return Marshal.load(Marshal.dump([:foo, :bar]))")
        assert self.unwrap(space, w_res) == ["foo", "bar"]

        w_res = space.execute("return Marshal.load(Marshal.dump(['foo', 'bar']))")
        assert self.unwrap(space, w_res) == ["foo", "bar"]

    def test_incompatible_format(self, space):
        with self.raises(
            space,
            "TypeError",
            "incompatible marshal file format (can't be read)\n"
            "format version 4.8 required; 97.115 given"
        ):
            space.execute("Marshal.load('asd')")

    def test_short_data(self, space):
        with self.raises(space, "ArgumentError", "marshal data too short"):
            space.execute("Marshal.load('')")

    def test_parameters(self, space):
        with self.raises(space, "TypeError", "instance of IO needed"):
            space.execute("Marshal.load(4)")

    def test_io(self, space, tmpdir):
        f = tmpdir.join("testfile")

        w_res = space.execute("""
        Marshal.dump('hallo', File.new('%s', 'wb'))
        file = File.open('%s', 'rb')
        return Marshal.load(file.read)
        """ % (f, f))
        assert space.str_w(w_res) == "hallo"

        w_res = space.execute("""
        Marshal.dump('hallo', File.new('%s', 'wb'))
        file = File.open('%s', 'rb')
        return Marshal.load(file)
        """ % (f, f))
        assert space.str_w(w_res) == "hallo"
