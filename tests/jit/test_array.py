from .base import BaseJITTest


class TestArray(BaseJITTest):
    def test_subscript_assign_simple(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        arr = [false]
        10000.times { arr[0] = true }
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p7, p8, p10, p13, i74, p21, p24, p26, p28, i40, p37, p67, p56, p43, p42, p46, p53, p47, p45, p51, descr=TargetToken(4311183872))
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at LOAD_SELF')
        debug_merge_point(0, 0, 'times at SEND')
        setfield_gc(p28, 42, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101e2c548>)
        p76 = force_token()
        i77 = int_lt(i74, i40)
        guard_true(i77, descr=<Guard0x101e2c4d0>)
        debug_merge_point(0, 0, 'times at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at YIELD')
        p78 = force_token()
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at LOAD_CONST')
        debug_merge_point(1, 1, 'block in <main> at BUILD_ARRAY')
        debug_merge_point(1, 1, 'block in <main> at LOAD_CONST')
        debug_merge_point(1, 1, 'block in <main> at BUILD_ARRAY')
        debug_merge_point(1, 1, 'block in <main> at SEND_SPLAT')
        p79 = force_token()
        i80 = getfield_gc(p67, descr=<FieldS list.length 8>)
        i81 = int_ge(0, i80)
        setfield_gc(p28, 20, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_false(i81, descr=<Guard0x101e2c3e0>)
        p82 = getfield_gc(p67, descr=<FieldP list.items 16>)
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        debug_merge_point(0, 0, 'times at DISCARD_TOP')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        debug_merge_point(0, 0, 'times at LOAD_CONST')
        debug_merge_point(0, 0, 'times at SEND')
        p83 = force_token()
        i84 = int_add(i74, 1)
        debug_merge_point(0, 0, 'times at STORE_DEREF')
        debug_merge_point(0, 0, 'times at DISCARD_TOP')
        debug_merge_point(0, 0, 'times at JUMP')
        debug_merge_point(0, 0, 'times at LOAD_DEREF')
        setfield_gc(p28, 63, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setarrayitem_gc(p82, 0, ConstPtr(ptr58), descr=<ArrayP 8>)
        i85 = arraylen_gc(p51, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p8, p10, p13, i84, p21, p24, p26, p28, i40, p37, p67, p56, p43, p42, p46, p53, p47, p45, p51, descr=TargetToken(4311183872))
        """)
