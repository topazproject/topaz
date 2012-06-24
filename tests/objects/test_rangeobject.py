from ..base import BaseRuPyPyTest
import py


class TestRangeObject(BaseRuPyPyTest):
    def test_new(self, space):
        w_res = space.execute("return Range.new(1, 2)")
        assert space.int_w(w_res.w_start) == 1
        assert space.int_w(w_res.w_end) == 2
        assert w_res.exclusive == False
    
    def test_map(self, space):
        w_res = space.execute("return (1..3).map {|x| x * 5}")
        assert self.unwrap(space, w_res) == [5, 10, 15]
        
        w_res = space.execute("return (1...3).map {|x| x * 5}")
        assert self.unwrap(space, w_res) == [5, 10]

    def test_starting_point_always_returned(self, space):
        w_res = space.execute("return (1..1).map {|x| x}")
        assert self.unwrap(space, w_res) == [1]

    def test_to_a(self, space):
        w_res = space.execute("return (1..3).to_a")
        assert self.unwrap(space, w_res) == [1, 2, 3]
        
        w_res = space.execute("return (1...3).to_a")
        assert self.unwrap(space, w_res) == [1, 2]
        
        w_res = space.execute("return (3..2).to_a")
        assert self.unwrap(space, w_res) == []

    def test_alphanumeric_values(self, space):
        w_res = space.execute("return ('a'..'e').to_a")
        assert self.unwrap(space, w_res) == ['a', 'b', 'c', 'd', 'e']

    def test_begin(self, space):
        w_res = space.execute("return (5..10).begin")
        assert self.unwrap(space, w_res) == 5

    def test_end(self, space):
        w_res = space.execute("return (5..10).end")
        assert self.unwrap(space, w_res) == 10
        
        w_res = space.execute("return (5...10).end")
        assert self.unwrap(space, w_res) == 10

    def test_exclude_end(self, space):
        w_res = space.execute("return (1..5).exclude_end?")
        assert self.unwrap(space, w_res) == False
        
        w_res = space.execute("return (1...5).exclude_end?")
        assert self.unwrap(space, w_res) == True

    def test_cover(self, space):
        w_res = space.execute("return (1..5).cover?(5)")
        assert self.unwrap(space, w_res) == True
        
        w_res = space.execute("return (1...5).cover?(5)")
        assert self.unwrap(space, w_res) == False

    def test_eql(self, space):
        w_res = space.execute("return (1..2) == (1..2)")
        assert self.unwrap(space, w_res) == True
        
        w_res = space.execute("return (1...2) == (1...2)")
        assert self.unwrap(space, w_res) == True
        
        w_res = space.execute("return (1..2) == Range.new(1, 2)")
        assert self.unwrap(space, w_res) == True
        
        w_res = space.execute("return (1..2) == Range.new(1, 2, false)")
        assert self.unwrap(space, w_res) == True
        
        w_res = space.execute("return (1...2) == Range.new(1, 2, true)")
        assert self.unwrap(space, w_res) == True
        
        w_res = space.execute("return (1..2) == (1...2)")
        assert self.unwrap(space, w_res) == False

    def test_include(self, space):
        w_res = space.execute("return (1..5).include?(4)")
        assert self.unwrap(space, w_res) == True
        
        w_res = space.execute("return (1..5).include?(6)")
        assert self.unwrap(space, w_res) == False
        
        w_res = space.execute("return ('a'..'f').include?('c')")
        assert self.unwrap(space, w_res) == True