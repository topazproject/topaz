from .base import BaseJITTest


class TestArray(BaseJITTest):
    def test_subscript_assign_simple(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        arr = [false]
        10000.times { arr[0] = true }
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p2, p4, p5, p6, p7, p9, p10, p13, i71, p21, p24, p26, p28, i40, p52, p57, p63, p50, p67, descr=TargetToken(140266976448368))
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at LOAD_SELF')
        debug_merge_point(0, 0, 'times at SEND')
        setfield_gc(p28, 42, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x7f92735b8f28>)
        p76 = force_token()
        i77 = int_lt(i71, i40)
        guard_true(i77, descr=<Guard0x7f92734f8f98>)
        debug_merge_point(0, 0, 'times at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at YIELD')
        p78 = force_token()
        enter_portal_frame(0, 0)
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at LOAD_CONST')
        debug_merge_point(1, 1, 'block in <main> at BUILD_ARRAY')
        debug_merge_point(1, 1, 'block in <main> at LOAD_CONST')
        debug_merge_point(1, 1, 'block in <main> at BUILD_ARRAY')
        debug_merge_point(1, 1, 'block in <main> at SEND_SPLAT')
        p81 = force_token()
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        leave_portal_frame(0)
        debug_merge_point(0, 0, 'times at DISCARD_TOP')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at LOAD_CONST')
        debug_merge_point(0, 0, 'times at SEND')
        p83 = force_token()
        i85 = int_add(i71, 1)
        debug_merge_point(0, 0, 'times at STORE_DEREF')
        debug_merge_point(0, 0, 'times at DISCARD_TOP')
        debug_merge_point(0, 0, 'times at JUMP')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        i86 = arraylen_gc(p50, descr=<ArrayP 8>)
        i87 = arraylen_gc(p67, descr=<ArrayP 8>)
        setfield_gc(p28, 63, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p2, p4, p5, p6, p7, p9, p10, p13, i85, p21, p24, p26, p28, i40, p52, p57, p63, p50, p67, descr=TargetToken(140266976448368))
        """)
