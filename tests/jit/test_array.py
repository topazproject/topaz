from .base import BaseJITTest


class TestArray(BaseJITTest):
    def test_subscript_assign_simple(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        arr = [false]
        10000.times { arr[0] = true }
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p7, p9, p12, i66, p20, p23, p25, p27, i39, p36, p48, p63, descr=TargetToken(4323626640))
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at LOAD_SELF')
        debug_merge_point(0, 0, 'times at SEND')
        setfield_gc(p27, 42, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101c0b1f0>)
        p69 = force_token()
        i70 = int_lt(i66, i39)
        guard_true(i70, descr=<Guard0x101c0b178>)
        debug_merge_point(0, 0, 'times at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at YIELD')
        p71 = force_token()
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at LOAD_CONST')
        debug_merge_point(1, 1, 'block in <main> at BUILD_ARRAY')
        debug_merge_point(1, 1, 'block in <main> at LOAD_CONST')
        debug_merge_point(1, 1, 'block in <main> at BUILD_ARRAY')
        debug_merge_point(1, 1, 'block in <main> at SEND_SPLAT')
        p72 = force_token()
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        debug_merge_point(0, 0, 'times at DISCARD_TOP')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at LOAD_CONST')
        debug_merge_point(0, 0, 'times at SEND')
        p73 = force_token()
        i74 = int_add(i66, 1)
        debug_merge_point(0, 0, 'times at STORE_DEREF')
        debug_merge_point(0, 0, 'times at DISCARD_TOP')
        debug_merge_point(0, 0, 'times at JUMP')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        setfield_gc(p27, 63, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        i75 = arraylen_gc(p48, descr=<ArrayP 8>)
        i76 = arraylen_gc(p63, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p9, p12, i74, p20, p23, p25, p27, i39, p36, p48, p63, descr=TargetToken(4323626640))
        """)
