import pytest

from topaz.mapdict import ClassNode

from .base import BaseTopazTest


class FakeObject(object):
    storage = None

    def __init__(self, map):
        self.map = map


class TestMapDict(BaseTopazTest):
    @pytest.mark.parametrize("i", range(10))
    def test_simple_size_estimation(self, space, i):
        class_node = ClassNode(i)
        assert class_node.size_estimate() == 0

        for j in range(1000):
            w_obj = FakeObject(class_node)
            for a in "abcdefghij"[:i]:
                w_obj.map.add_attr(space, w_obj, a)
        assert class_node.size_estimate() == i

    @pytest.mark.parametrize("i", range(1, 10))
    def test_avg_size_estimation(self, space, i):
        class_node = ClassNode(i)
        assert class_node.size_estimate() == 0

        for j in range(1000):
            w_obj = FakeObject(class_node)
            for a in "abcdefghij"[:i]:
                w_obj.map.add_attr(space, w_obj, a)
            w_obj = FakeObject(class_node)
            for a in "klmnopqars":
                w_obj.map.add_attr(space, w_obj, a)
        assert class_node.size_estimate() in [(i + 10) // 2, (i + 11) // 2]
