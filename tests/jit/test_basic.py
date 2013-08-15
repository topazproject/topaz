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
        label(p0, p1, p3, p4, p5, p6, p7, p10, i35, p20, p22, p28, descr=TargetToken(4310781936))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p22, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x100febda8>)
        p37 = force_token()
        i38 = int_lt(i35, 10000)
        guard_true(i38, descr=<Guard0x100febcb8>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p39 = force_token()
        i40 = int_add(i35, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p22, 35, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p3, p4, p5, p6, p7, p10, i40, p20, p22, p28, descr=TargetToken(4310781936))
        """)

    def test_constant_string(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        i = 0
        while i < 10000
          i += "a".length
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p7, p10, i36, p20, p22, p28, descr=TargetToken(4310781936))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p22, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x100ff6818>)
        p38 = force_token()
        i39 = int_lt(i36, 10000)
        guard_true(i39, descr=<Guard0x100ff6728>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at COERCE_STRING')
        debug_merge_point(0, 0, '<main> at SEND')
        p40 = force_token()
        debug_merge_point(0, 0, '<main> at SEND')
        p41 = force_token()
        i42 = int_add(i36, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p22, 41, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p3, p4, p5, p6, p7, p10, i42, p20, p22, p28, descr=TargetToken(4310781936))
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
        label(p0, p1, p3, p4, p5, p7, p10, i56, p19, p22, p24, p30, descr=TargetToken(4310782288))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p24, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101e21e20>)
        p59 = force_token()
        i60 = int_lt(i56, 10000)
        guard_true(i60, descr=<Guard0x101e209f8>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SCOPE')
        debug_merge_point(0, 0, '<main> at LOAD_LOCAL_CONSTANT')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p61 = force_token()
        debug_merge_point(1, 1, 'try_convert at LOAD_SCOPE')
        debug_merge_point(1, 1, 'try_convert at LOAD_LOCAL_CONSTANT')
        debug_merge_point(1, 1, 'try_convert at LOAD_DEREF')
        debug_merge_point(1, 1, 'try_convert at LOAD_SCOPE')
        debug_merge_point(1, 1, 'try_convert at LOAD_LOCAL_CONSTANT')
        debug_merge_point(1, 1, 'try_convert at LOAD_CONST')
        debug_merge_point(1, 1, 'try_convert at SEND')
        p62 = force_token()
        p63 = force_token()
        p64 = force_token()
        p65 = force_token()
        p66 = force_token()
        p67 = force_token()
        p68 = force_token()
        p69 = force_token()
        p70 = force_token()
        p71 = force_token()
        p72 = force_token()
        debug_merge_point(1, 1, 'try_convert at RETURN')
        p73 = force_token()
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p74 = force_token()
        i75 = int_add(i56, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p24, 48, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setfield_gc(p1, p73, descr=<FieldP topaz.frame.Frame.vable_token 32>)
        jump(p0, p1, p3, p4, p5, p7, p10, i75, p19, p22, p24, p30, descr=TargetToken(4310782288))
        """)
