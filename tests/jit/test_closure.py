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
        label(p0, p1, p2, p4, p5, p6, p7, p9, p10, p13, i86, p21, p23, p25, p27, p29, p31, p33, p35, p38, p40, p42, p55, i59, p53, p74, p79, p72, descr=TargetToken(139914354759008))
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at LOAD_SELF')
        debug_merge_point(0, 0, 'each at SEND')
        setfield_gc(p42, 291, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x7f405a879198>)
        p90 = force_token()
        debug_merge_point(0, 0, 'each at SEND')
        p91 = force_token()
        setfield_gc(p42, 296, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        i93 = int_lt(i86, i59)
        guard_true(i93, descr=<Guard0x7f405a879268>)
        debug_merge_point(0, 0, 'each at LOAD_CONST')
        debug_merge_point(0, 0, 'each at SEND')
        p94 = force_token()
        debug_merge_point(0, 0, 'each at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at YIELD')
        p95 = force_token()
        enter_portal_frame(0, 0)
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at STORE_DEREF')
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        leave_portal_frame(0)
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at SEND')
        p99 = force_token()
        enter_portal_frame(0, 0)
        debug_merge_point(1, 2, 'succ at LOAD_SELF')
        debug_merge_point(1, 2, 'succ at LOAD_CONST')
        debug_merge_point(1, 2, 'succ at SEND')
        p102 = force_token()
        i104 = int_add(i86, 1)
        debug_merge_point(1, 2, 'succ at RETURN')
        leave_portal_frame(0)
        debug_merge_point(0, 0, 'each at STORE_DEREF')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at JUMP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        setfield_gc(p79, i86, descr=<FieldS topaz.objects.intobject.W_FixnumObject.inst_intvalue 8 pure>)
        i106 = arraylen_gc(p72, descr=<ArrayP 8>)
        setfield_gc(p42, 9, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p2, p4, p5, p6, p7, p9, p10, p13, i104, p21, p23, p25, p27, p29, p31, p33, p35, p38, p40, p42, p55, i59, p53, p74, p79, p72, descr=TargetToken(139914354759008))
        """)
