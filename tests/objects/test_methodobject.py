from topaz.objects.methodobject import W_MethodObject, W_UnboundMethodObject

from ..base import BaseTopazTest


class TestMethodObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("Method")

    def test_to_s(self, space):
        w_res = space.execute("return 'test'.method(:to_s).to_s")
        assert space.str_w(w_res) == "#<Method: String#to_s>"

    def test_allocate(self, space):
        with self.raises(space, "TypeError", "allocator undefined for Method"):
            space.execute("Method.allocate")

    def test_owner(self, space):
        w_res = space.execute("return 'test'.method(:to_s).owner")
        assert w_res == space.w_string

    def test_unbind(self, space):
        w_res = space.execute("return 'test'.method(:to_s).unbind.class")
        assert w_res == space.getclassfor(W_UnboundMethodObject)

    def test_receiver(self, space):
        w_res = space.execute("""
        a = 'test'
        return a.method(:to_s).receiver == a
        """)
        assert self.unwrap(space, w_res) is True

    def test_eql(self, space):
        w_res = space.execute("return 'test'.method(:to_s) == 'test'.method(:to_s)")
        assert self.unwrap(space, w_res) is False
        w_res = space.execute("""
        a = 'test'
        return a.method(:to_s) == a.method(:to_s)
        """)
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("""
        a = 'test'
        return a.method(:to_s) == a.method(:==)
        """)
        assert self.unwrap(space, w_res) is False

    def test_call(self, space):
        w_res = space.execute("""
        return 'test'.method(:to_s).call
        """)
        assert self.unwrap(space, w_res) == "test"

        w_res = space.execute("""
        return 'test'.method(:to_s).unbind.bind('hello').call
        """)
        assert self.unwrap(space, w_res) == "hello"

        with self.raises(space, "TypeError", "bind argument must be an instance of String"):
            w_res = space.execute("""
            return 'test'.method(:to_s).unbind.bind(1)
            """)


class TestUnboundObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("UnboundMethod")

    def test_to_s(self, space):
        w_res = space.execute("return 'test'.method(:to_s).unbind.to_s")
        assert space.str_w(w_res) == "#<UnboundMethod: String#to_s>"

    def test_allocate(self, space):
        with self.raises(space, "TypeError", "allocator undefined for UnboundMethod"):
            space.execute("return UnboundMethod.allocate")

    def test_owner(self, space):
        w_res = space.execute("return 'test'.method(:to_s).owner")
        assert w_res == space.w_string

    def test_bind(self, space):
        w_res = space.execute("""
        r = 'another'
        m = 'test'.method(:to_s).unbind.bind(r)
        return r == m.receiver, m.class
        """)
        assert self.unwrap(space, w_res) == [True, space.getclassfor(W_MethodObject)]

    def test_eql(self, space):
        w_res = space.execute("return 'test'.method(:to_s).unbind == 'test'.method(:to_s).unbind")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return 'test'.method(:to_s).unbind == 'test'.method(:==).unbind")
        assert self.unwrap(space, w_res) is False
