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
        label(p0, p1, p3, p4, p5, p6, p7, p9, i78, p14, p20, p22, p24, p26, p29, p31, f51, p45, p44, p66, descr=TargetToken(140411363672184))
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        guard_not_invalidated(descr=<Guard21>)
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at SEND')
        i80 = force_token()
        f81 = cast_int_to_float(i78)
        i82 = float_lt(f81, f51)
        guard_true(i82, descr=<Guard22>)
        debug_merge_point(0, 0, 'each at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at YIELD')
        i83 = force_token()
        debug_merge_point(1, 1, 'block in foo at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in foo at STORE_DEREF')
        debug_merge_point(1, 1, 'block in foo at RETURN')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at LOAD_CONST')
        debug_merge_point(0, 0, 'each at SEND')
        i84 = force_token()
        setfield_gc(p66, i78, descr=<FieldS topaz.closure.IntCell.inst_intvalue 8>)
        i85 = int_add_ovf(i78, 1)
        guard_no_overflow(descr=<Guard23>)
        debug_merge_point(0, 0, 'each at STORE_DEREF')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at JUMP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        jump(p0, p1, p3, p4, p5, p6, p7, p9, i85, p14, p20, p22, p24, p26, p29, p31, f51, p45, p44, p66, descr=TargetToken(140411363672184))
        """)
