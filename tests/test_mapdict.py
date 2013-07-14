import pytest

from topaz import mapdict


class FakeObject(object):
    def __init__(self, map):
        self.map = map
        self.object_storage = self.unboxed_storage = None


class TestMapDict(object):
    @pytest.mark.parametrize("i", range(10))
    def test_simple_size_estimation(self, space, i):
        class_node = mapdict.ClassNode(i)
        assert class_node.size_estimate.object_size_estimate() == 0
        assert class_node.size_estimate.unboxed_size_estimate() == 0

        for j in range(1000):
            w_obj = FakeObject(class_node)
            for a in "abcdefghij"[:i]:
                w_obj.map = w_obj.map.add(space, mapdict.ObjectAttributeNode, a, w_obj)
        assert class_node.size_estimate.object_size_estimate() == i
        assert class_node.size_estimate.unboxed_size_estimate() == 0

    @pytest.mark.parametrize("i", range(1, 10))
    def test_avg_size_estimation(self, space, i):
        class_node = mapdict.ClassNode(i)
        assert class_node.size_estimate.object_size_estimate() == 0
        assert class_node.size_estimate.unboxed_size_estimate() == 0

        for j in range(1000):
            w_obj = FakeObject(class_node)
            for a in "abcdefghij"[:i]:
                w_obj.map = w_obj.map.add(space, mapdict.ObjectAttributeNode, a, w_obj)
            w_obj = FakeObject(class_node)
            for a in "klmnopqars":
                w_obj.map = w_obj.map.add(space, mapdict.ObjectAttributeNode, a, w_obj)

        assert class_node.size_estimate.object_size_estimate() in [(i + 10) // 2, (i + 11) // 2]
        assert class_node.size_estimate.unboxed_size_estimate() == 0
