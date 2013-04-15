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
        label(p0, p1, p3, p4, p5, p6, p7, p9, p12, i67, p20, p22, p24, p27, p29, p31, i48, p42, p61, p59, descr=TargetToken(4323625760))
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at LOAD_SELF')
        debug_merge_point(0, 0, 'each at SEND')
        setfield_gc(p31, 171, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101c0cea8>)
        p71 = force_token()
        debug_merge_point(0, 0, 'each at SEND')
        p72 = force_token()
        setfield_gc(p31, 176, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        i73 = int_lt(i67, i48)
        guard_true(i73, descr=<Guard0x101c0ce30>)
        debug_merge_point(0, 0, 'each at LOAD_CONST')
        debug_merge_point(0, 0, 'each at SEND')
        p74 = force_token()
        debug_merge_point(0, 0, 'each at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at YIELD')
        p75 = force_token()
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at STORE_DEREF')
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at SEND')
        p76 = force_token()
        debug_merge_point(1, 2, 'succ at LOAD_SELF')
        debug_merge_point(1, 2, 'succ at LOAD_CONST')
        debug_merge_point(1, 2, 'succ at SEND')
        p77 = force_token()
        i78 = int_add(i67, 1)
        debug_merge_point(1, 2, 'succ at RETURN')
        debug_merge_point(0, 0, 'each at STORE_DEREF')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at JUMP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        setfield_gc(p31, 9, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setfield_gc(p61, i67, descr=<FieldS topaz.closure.IntCell.inst_intvalue 16>)
        i79 = arraylen_gc(p59, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p9, p12, i78, p20, p22, p24, p27, p29, p31, i48, p42, p61, p59, descr=TargetToken(4323625760))
        """)
