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
        label(p0, p1, p3, p4, p5, p6, p9, i35, p19, p21, p27, p28, descr=TargetToken(4324574448))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p21, 21, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101c93268>)
        p37 = force_token()
        i38 = int_lt(i35, 10000)
        guard_true(i38, descr=<Guard0x101c93178>)
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
        setfield_gc(p21, 35, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p3, p4, p5, p6, p9, i40, p19, p21, p27, p28, descr=TargetToken(4324574448))
        """)

    def test_ivar_while_loop(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        @i = 0
        while @i < 10000
            @i += 1
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p9, p19, p41, p30, p31, p25, descr=TargetToken(4324590832))
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p19, 23, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101c8f970>)
        p43 = force_token()
        i44 = getfield_gc_pure(p41, descr=<FieldS topaz.objects.intobject.W_FixnumObject.inst_intvalue 8>)
        i45 = int_lt(i44, 10000)
        guard_true(i45, descr=<Guard0x101c8f8f8>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at DUP_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p46 = force_token()
        i47 = int_add(i44, 1)
        debug_merge_point(0, 0, '<main> at STORE_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        setfield_gc(p19, 39, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        p48 = new_with_vtable(4300565608)
        setfield_gc(p48, i47, descr=<FieldS topaz.objects.intobject.W_FixnumObject.inst_intvalue 8>)
        setarrayitem_gc(p25, 0, p48, descr=<ArrayP 8>)
        i49 = arraylen_gc(p25, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p9, p19, p48, p30, p31, p25, descr=TargetToken(4324590832))
        """)
