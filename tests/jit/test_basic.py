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
        label(p0, p1, p3, p4, p5, p6, p9, i34, p19, p21, p27, descr=TargetToken(4323625760))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p21, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101bf74c0>)
        p36 = force_token()
        i37 = int_lt(i34, 10000)
        guard_true(i37, descr=<Guard0x101bf7448>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p38 = force_token()
        i39 = int_add(i34, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p21, 35, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p3, p4, p5, p6, p9, i39, p19, p21, p27, descr=TargetToken(4323625760))
        """)

    def test_ivar_while_loop(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        @i = 0
        while @i < 10000
            @i += 1
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p9, p19, p40, p30, p25, descr=TargetToken(4323625760))
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p19, 23, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101bf3c40>)
        p42 = force_token()
        i43 = getfield_gc_pure(p40, descr=<FieldS topaz.objects.intobject.W_FixnumObject.inst_intvalue 8>)
        i44 = int_lt(i43, 10000)
        guard_true(i44, descr=<Guard0x101bf3bc8>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at DUP_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p45 = force_token()
        i46 = int_add(i43, 1)
        debug_merge_point(0, 0, '<main> at STORE_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        setfield_gc(p19, 39, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        p47 = new_with_vtable(4300487864)
        setfield_gc(p47, i46, descr=<FieldS topaz.objects.intobject.W_FixnumObject.inst_intvalue 8>)
        setarrayitem_gc(p25, 0, p47, descr=<ArrayP 8>)
        i48 = arraylen_gc(p25, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p9, p19, p47, p30, p25, descr=TargetToken(4323625760))
        """)

    def test_constant_string(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        i = 0
        while i < 10000
            i += "a".length
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p9, i35, p19, p21, p27, descr=TargetToken(4310789600))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p21, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x100fc35b0>)
        p37 = force_token()
        i38 = int_lt(i35, 10000)
        guard_true(i38, descr=<Guard0x100fc3538>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at COERCE_STRING')
        debug_merge_point(0, 0, '<main> at SEND')
        p39 = force_token()
        debug_merge_point(0, 0, '<main> at SEND')
        p40 = force_token()
        i41 = int_add(i35, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p21, 41, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p3, p4, p5, p6, p9, i41, p19, p21, p27, descr=TargetToken(4310789600))
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
        label(p0, p1, p3, p4, p6, p9, i55, p18, p21, p23, p29, descr=TargetToken(4323643288))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p23, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101c26c50>)
        p58 = force_token()
        i59 = int_lt(i55, 10000)
        guard_true(i59, descr=<Guard0x101c26bd8>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SCOPE')
        debug_merge_point(0, 0, '<main> at LOAD_LOCAL_CONSTANT')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p60 = force_token()
        debug_merge_point(1, 1, 'try_convert at LOAD_SCOPE')
        debug_merge_point(1, 1, 'try_convert at LOAD_LOCAL_CONSTANT')
        debug_merge_point(1, 1, 'try_convert at LOAD_DEREF')
        debug_merge_point(1, 1, 'try_convert at LOAD_SCOPE')
        debug_merge_point(1, 1, 'try_convert at LOAD_LOCAL_CONSTANT')
        debug_merge_point(1, 1, 'try_convert at LOAD_CONST')
        debug_merge_point(1, 1, 'try_convert at SEND')
        p61 = force_token()
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
        debug_merge_point(1, 1, 'try_convert at RETURN')
        p72 = force_token()
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p73 = force_token()
        i74 = int_add(i55, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p23, 48, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setfield_gc(p1, p72, descr=<FieldP topaz.frame.Frame.vable_token 32>)
        jump(p0, p1, p3, p4, p6, p9, i74, p18, p21, p23, p29, descr=TargetToken(4323643288))
        """)
