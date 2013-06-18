from rpython.rlib import rgc


class TestObjectSpace(object):
    def test_name(self, space):
        space.execute("ObjectSpace")

    def test_each_object(self, space, monkeypatch):
        space.execute("""
        class X
        end
        """)
        monkeypatch.setattr(rgc, "get_rpy_roots", lambda: [rgc._GcRef(space)])
        w_res = space.execute("""
        names = []
        ObjectSpace.each_object(Module) do |mod|
          names << mod.name
        end
        return names.include? "X"
        """)
        assert w_res is space.w_true
