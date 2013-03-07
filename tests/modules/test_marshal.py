from ..base import BaseTopazTest
import pytest


class TestMarshal(BaseTopazTest):
    def test_dump_constants(self, space):
        w_res = space.execute("return Marshal.dump(nil)")
        #assert space.str_w(w_res) == "\x04\b0"
        assert space.str_w(w_res) == "040830"

        w_res = space.execute("return Marshal.dump(true)")
        assert space.str_w(w_res) == "040854"

        w_res = space.execute("return Marshal.dump(false)")
        assert space.str_w(w_res) == "040846"

    def test_load_constants(self, space):
        w_res = space.execute("return Marshal.load('040830')")
        assert w_res == space.w_nil

        w_res = space.execute("return Marshal.load('040854')")
        assert space.is_true(w_res)

        w_res = space.execute("return Marshal.load('040846')")
        assert not space.is_true(w_res)

    def test_dump_integer(self, space):
        w_res = space.execute("return Marshal.dump(5)")
        assert space.str_w(w_res) == "0408690A"

        w_res = space.execute("return Marshal.dump(100)")
        assert space.str_w(w_res) == "04086969"

        w_res = space.execute("return Marshal.dump(0)")
        assert space.str_w(w_res) == "04086900"

        w_res = space.execute("return Marshal.dump(-1)")
        assert space.str_w(w_res) == "040869FA"

        w_res = space.execute("return Marshal.dump(-123)")
        assert space.str_w(w_res) == "04086980"

        w_res = space.execute("return Marshal.dump(122)")
        assert space.str_w(w_res) == "0408697F"

    def test_load_integer(self, space):
        w_res = space.execute("return Marshal.load('0408690A')")
        assert space.int_w(w_res) == 5

        w_res = space.execute("return Marshal.load('04086969')")
        assert space.int_w(w_res) == 100

        w_res = space.execute("return Marshal.load('04086900')")
        assert space.int_w(w_res) == 0

        w_res = space.execute("return Marshal.load('040869FA')")
        assert space.int_w(w_res) == -1

        w_res = space.execute("return Marshal.load('04086980')")
        assert space.int_w(w_res) == -123

        w_res = space.execute("return Marshal.load('0408697F')")
        assert space.int_w(w_res) == 122

    def test_dump_array(self, space):
        w_res = space.execute("return Marshal.dump([])")
        assert space.str_w(w_res) == "04085B00"

        w_res = space.execute("return Marshal.dump([nil])")
        assert space.str_w(w_res) == "04085B0630"

        w_res = space.execute("return Marshal.dump([nil, true, false])")
        assert space.str_w(w_res) == "04085B08305446"

    def test_load_array(self, space):
        w_res = space.execute("return Marshal.load('04085B00')")
        assert self.unwrap(space, w_res) == []

        w_res = space.execute("return Marshal.load('04085B0630')")
        assert self.unwrap(space, w_res) == [None]

        w_res = space.execute("return Marshal.load('04085B08305446')")
        assert self.unwrap(space, w_res) == [None, True, False]

    def test_dump_symbol(self, space):
        w_res = space.execute("return Marshal.dump(:abc)")
        assert space.str_w(w_res) == "04083A08616263"

    def test_load_symbol(self, space):
        w_res = space.execute("return Marshal.load('04083A08616263')")
        assert space.symbol_w(w_res) == "abc"

    def no_test_load_symbol(self, space):
        w_res = space.execute("return Marshal.load('04083a08616263')")
        assert self.unwrap(space, w_res) == ":abc"

    def test_dump_hash(self, space):
        w_res = space.execute("return Marshal.dump({})")
        assert space.str_w(w_res) == "04087B00"

        w_res = space.execute("return Marshal.dump({1 => 2, 3 => 4})")
        assert self.unwrap(space, w_res) == "04087B076906690769086909"

    def test_load_hash(self, space):
        w_res = space.execute("return Marshal.load('04087B00')")
        assert self.unwrap(space, w_res) == {}

        w_res = space.execute("return Marshal.load('04087B076906690769086909')")
        assert self.unwrap(space, w_res) == {1: 2, 3: 4}

    def no_dump_string(self, space):
        w_res = space.execute("return Marshal.dump('abc'))")
        assert space.str_w(w_res) == "0408492208616263063A064554"

    def no_load_string(self, space):
        w_res = space.execute("return Marshal.load('0408492208616263063a064554')")
        assert space.str_w(w_res) == "asd"

    def no_test_array(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump([1,2,3]))")
        assert self.unwrap(space, w_res) == [1, 2, 3]

        w_res = space.execute("return Marshal.load(Marshal.dump([1,[2,3],4]))")
        assert self.unwrap(space, w_res) == [1, [2, 3], 4]
