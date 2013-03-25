class Compare(object):
    @staticmethod
    def compare(space, a, b, block=None):
        if block is None:
            w_cmp_res = space.send(a, space.newsymbol("<=>"), [b])
        else:
            w_cmp_res = space.invoke_block(block, [a, b])
        if w_cmp_res is space.w_nil:
            raise space.error(
                space.w_ArgumentError,
                "comparison of %s with %s failed" %
                (space.obj_to_s(space.getclass(a)),
                    space.obj_to_s(space.getclass(b)))
            )
        else:
            return w_cmp_res