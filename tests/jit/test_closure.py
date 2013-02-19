from .base import BaseJITTest


class TestClosure(BaseJITTest):
    def test_int_closure_cells(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        a = 1
        (1..10_000).each do |i|
          a = i
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p7, p9, p12, i78, p20, p22, p24, p26, p28, p31, p33, i56, p46, p45, p70, p68, descr=TargetToken(139879579074768))
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        guard_not_invalidated(descr=<Guard17>)
        debug_merge_point(0, 0, 'each at LOAD_SELF')
        debug_merge_point(0, 0, 'each at SEND')
        i82 = force_token()
        debug_merge_point(0, 0, 'each at SEND')
        i83 = force_token()
        i84 = int_lt(i78, i56)
        guard_true(i84, descr=<Guard18>)
        debug_merge_point(0, 0, 'each at LOAD_CONST')
        debug_merge_point(0, 0, 'each at SEND')
        i85 = force_token()
        debug_merge_point(0, 0, 'each at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at YIELD')
        i86 = force_token()
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at STORE_DEREF')
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at SEND')
        i87 = force_token()
        debug_merge_point(1, 2, 'succ at LOAD_SELF')
        debug_merge_point(1, 2, 'succ at LOAD_CONST')
        debug_merge_point(1, 2, 'succ at SEND')
        i88 = force_token()
        i89 = int_add(i78, 1)
        debug_merge_point(1, 2, 'succ at RETURN')
        debug_merge_point(0, 0, 'each at STORE_DEREF')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at JUMP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        setfield_gc(p70, i78, descr=<FieldS topaz.closure.IntCell.inst_intvalue 16>)
        i90 = arraylen_gc(p68, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p9, p12, i89, p20, p22, p24, p26, p28, p31, p33, i56, p46, p45, p70, p68, descr=TargetToken(139879579074768))
        """)
