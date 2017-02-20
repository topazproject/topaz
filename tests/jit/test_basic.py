from .base import BaseJITTest


class TestBasic(BaseJITTest):
    def test_while_loop(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        i = 0
        while i < 10000
          i += 1
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p2, p4, p6, p7, p9, p10, i35, p20, p22, descr=TargetToken(140471158509584))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p22, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x7fc1fe888ec0>)
        p38 = force_token()
        i40 = int_lt(i35, 10000)
        guard_true(i40, descr=<Guard0x7fc1fd828b60>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p41 = force_token()
        i43 = int_add(i35, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p22, 35, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p2, p4, p6, p7, p9, p10, i43, p20, p22, descr=TargetToken(140471158509584))
        """)

    def test_constant_string(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        i = 0
        while i < 10000
          i += "a".length
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p2, p4, p6, p7, p9, p10, i36, p20, p22, descr=TargetToken(140237115101120))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p22, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x7f8b7f7b9610>)
        p39 = force_token()
        i41 = int_lt(i36, 10000)
        guard_true(i41, descr=<Guard0x7f8b7f6f8a88>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at COERCE_STRING')
        debug_merge_point(0, 0, '<main> at SEND')
        p42 = force_token()
        debug_merge_point(0, 0, '<main> at SEND')
        p43 = force_token()
        i45 = int_add(i36, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p22, 41, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p2, p4, p6, p7, p9, p10, i45, p20, p22, descr=TargetToken(140237115101120))
        """)

    def test_method_missing(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        i = 0
        while i < 10000
          Array.try_convert(1)
          i += 1
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p2, p4, p6, p9, p10, i55, p19, p22, p24, descr=TargetToken(140138637040144))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p24, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x7f7491bb9610>)
        p58 = force_token()
        i60 = int_lt(i55, 10000)
        guard_true(i60, descr=<Guard0x7f7491af94f0>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SCOPE')
        debug_merge_point(0, 0, '<main> at LOAD_LOCAL_CONSTANT')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p61 = force_token()
        enter_portal_frame(0, 0)
        debug_merge_point(1, 1, 'try_convert at LOAD_SCOPE')
        debug_merge_point(1, 1, 'try_convert at LOAD_LOCAL_CONSTANT')
        debug_merge_point(1, 1, 'try_convert at LOAD_DEREF')
        debug_merge_point(1, 1, 'try_convert at LOAD_SCOPE')
        debug_merge_point(1, 1, 'try_convert at LOAD_LOCAL_CONSTANT')
        debug_merge_point(1, 1, 'try_convert at LOAD_CONST')
        debug_merge_point(1, 1, 'try_convert at SEND')
        p64 = force_token()
        p65 = force_token()
        p66 = force_token()
        p67 = force_token()
        p68 = force_token()
        p69 = force_token()
        p70 = force_token()
        p71 = force_token()
        p72 = force_token()
        p73 = force_token()
        debug_merge_point(1, 1, 'try_convert at RETURN')
        leave_portal_frame(0)
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p75 = force_token()
        i77 = int_add(i55, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p1, p73, descr=<FieldP topaz.frame.Frame.vable_token 32>)
        setfield_gc(p24, 48, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p2, p4, p6, p9, p10, i77, p19, p22, p24, descr=TargetToken(140138637040144))
        """)
