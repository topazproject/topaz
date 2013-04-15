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
