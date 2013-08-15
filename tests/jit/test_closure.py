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
        label(p0, p1, p3, p4, p5, p6, p7, p8, p10, p13, i80, p21, p23, p25, p27, p29, p31, p33, p35, p38, p40, p42, i59, p53, p74, p72, descr=TargetToken(4310782200))
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at LOAD_SELF')
        debug_merge_point(0, 0, 'each at SEND')
        setfield_gc(p42, 291, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x100f633d0>)
        p84 = force_token()
        debug_merge_point(0, 0, 'each at SEND')
        p85 = force_token()
        setfield_gc(p42, 296, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        i86 = int_lt(i80, i59)
        guard_true(i86, descr=<Guard0x100f63358>)
        debug_merge_point(0, 0, 'each at LOAD_CONST')
        debug_merge_point(0, 0, 'each at SEND')
        p87 = force_token()
        debug_merge_point(0, 0, 'each at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at YIELD')
        p88 = force_token()
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at STORE_DEREF')
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at SEND')
        p89 = force_token()
        debug_merge_point(1, 2, 'succ at LOAD_SELF')
        debug_merge_point(1, 2, 'succ at LOAD_CONST')
        debug_merge_point(1, 2, 'succ at SEND')
        p90 = force_token()
        i91 = int_add(i80, 1)
        debug_merge_point(1, 2, 'succ at RETURN')
        debug_merge_point(0, 0, 'each at STORE_DEREF')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at JUMP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        setfield_gc(p42, 9, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setfield_gc(p74, i80, descr=<FieldS topaz.closure.IntCell.inst_intvalue 16>)
        i92 = arraylen_gc(p72, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p8, p10, p13, i91, p21, p23, p25, p27, p29, p31, p33, p35, p38, p40, p42, i59, p53, p74, p72, descr=TargetToken(4310782200))
        """)
