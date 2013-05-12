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
        label(p0, p1, p3, p4, p5, p6, p7, p9, p12, i77, p20, p22, p24, p26, p28, p30, p32, p34, p37, p39, p41, i58, p52, p71, p69, descr=TargetToken(4323618096))
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at LOAD_SELF')
        debug_merge_point(0, 0, 'each at SEND')
        setfield_gc(p41, 291, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101c222f0>)
        p81 = force_token()
        debug_merge_point(0, 0, 'each at SEND')
        p82 = force_token()
        setfield_gc(p41, 296, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        i83 = int_lt(i77, i58)
        guard_true(i83, descr=<Guard0x101c22278>)
        debug_merge_point(0, 0, 'each at LOAD_CONST')
        debug_merge_point(0, 0, 'each at SEND')
        p84 = force_token()
        debug_merge_point(0, 0, 'each at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at YIELD')
        p85 = force_token()
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at STORE_DEREF')
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at SEND')
        p86 = force_token()
        debug_merge_point(1, 2, 'succ at LOAD_SELF')
        debug_merge_point(1, 2, 'succ at LOAD_CONST')
        debug_merge_point(1, 2, 'succ at SEND')
        p87 = force_token()
        i88 = int_add(i77, 1)
        debug_merge_point(1, 2, 'succ at RETURN')
        debug_merge_point(0, 0, 'each at STORE_DEREF')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at JUMP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        setfield_gc(p41, 9, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setfield_gc(p71, i77, descr=<FieldS topaz.closure.IntCell.inst_intvalue 16>)
        i89 = arraylen_gc(p69, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p9, p12, i88, p20, p22, p24, p26, p28, p30, p32, p34, p37, p39, p41, i58, p52, p71, p69, descr=TargetToken(4323618096))
        """)
