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
        label(p0, p1, p3, p4, p5, p6, p7, p9, p12, i75, p20, p22, p24, p26, p28, p31, p33, p35, i55, p46, p47, p68, p66, descr=TargetToken(4324574536))
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at LOAD_SELF')
        debug_merge_point(0, 0, 'each at SEND')
        setfield_gc(p35, 188, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101dacbd8>)
        p78 = force_token()
        debug_merge_point(0, 0, 'each at SEND')
        p79 = force_token()
        setfield_gc(p35, -1, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        i80 = int_lt(i75, i55)
        guard_true(i80, descr=<Guard0x101dacb60>)
        debug_merge_point(0, 0, 'each at LOAD_CONST')
        debug_merge_point(0, 0, 'each at SEND')
        p81 = force_token()
        debug_merge_point(0, 0, 'each at JUMP_IF_FALSE')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at YIELD')
        p82 = force_token()
        debug_merge_point(1, 1, 'block in <main> at LOAD_DEREF')
        debug_merge_point(1, 1, 'block in <main> at STORE_DEREF')
        debug_merge_point(1, 1, 'block in <main> at RETURN')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        debug_merge_point(0, 0, 'each at SEND')
        p83 = force_token()
        debug_merge_point(1, 2, 'succ at LOAD_SELF')
        debug_merge_point(1, 2, 'succ at LOAD_CONST')
        debug_merge_point(1, 2, 'succ at SEND')
        p84 = force_token()
        i85 = int_add(i75, 1)
        debug_merge_point(1, 2, 'succ at RETURN')
        debug_merge_point(0, 0, 'each at STORE_DEREF')
        debug_merge_point(0, 0, 'each at DISCARD_TOP')
        debug_merge_point(0, 0, 'each at JUMP')
        debug_merge_point(0, 0, 'each at LOAD_DEREF')
        setfield_gc(p35, 9, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setfield_gc(p68, i75, descr=<FieldS topaz.closure.IntCell.inst_intvalue 16>)
        i86 = arraylen_gc(p66, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p9, p12, i85, p20, p22, p24, p26, p28, p31, p33, p35, i55, p46, p47, p68, p66, descr=TargetToken(4324574536))
        """)
