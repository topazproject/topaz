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
        label(p0, p1, p3, p4, p5, p6, p9, i37, p19, p28, p29, descr=TargetToken(4309991544))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        guard_not_invalidated(descr=<Guard10>)
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        i38 = force_token()
        i39 = int_lt(i37, 10000)
        guard_true(i39, descr=<Guard11>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        i40 = force_token()
        i41 = int_add(i37, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        jump(p0, p1, p3, p4, p5, p6, p9, i41, p19, p28, p29, descr=TargetToken(4309991544))
        """)

    def test_ivar_while_loop(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        @i = 0
        while @i < 10000
            @i += 1
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p9, p42, p31, p32, p24, descr=TargetToken(140148740726904))
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        guard_not_invalidated(descr=<Guard10>)
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        i44 = force_token()
        i45 = getfield_gc_pure(p42, descr=<FieldS topaz.objects.intobject.W_FixnumObject.inst_intvalue 8>)
        i46 = int_lt(i45, 10000)
        guard_true(i46, descr=<Guard11>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at DUP_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        i47 = force_token()
        i48 = int_add(i45, 1)
        debug_merge_point(0, 0, '<main> at STORE_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        p49 = new_with_vtable(10493168)
        setfield_gc(p49, i48, descr=<FieldS topaz.objects.intobject.W_FixnumObject.inst_intvalue 8>)
        setarrayitem_gc(p24, 0, p49, descr=<ArrayP 8>)
        i50 = arraylen_gc(p24, descr=<ArrayP 8>)
        jump(p0, p1, p3, p4, p5, p6, p9, p49, p31, p32, p24, descr=TargetToken(140148740726904))
         """)
