from .base import BaseJITTest


class TestInstanceVars(BaseJITTest):
    def test_initialize(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        class A
          def initialize
            @a = 1
            @b = 2
            @c = 3
          end
        end
        i = 0
        while i < 10000
          A.new
          i += 1
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p7, p10, i41, p19, p22, p24, p30, descr=TargetToken(4310782288))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p24, 34, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x100f63808>)
        p43 = force_token()
        i44 = int_lt(i41, 10000)
        guard_true(i44, descr=<Guard0x100f63718>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SCOPE')
        debug_merge_point(0, 0, '<main> at LOAD_LOCAL_CONSTANT')
        debug_merge_point(0, 0, '<main> at SEND')
        p45 = force_token()
        p46 = force_token()
        p47 = force_token()
        debug_merge_point(1, 1, 'initialize at LOAD_SELF')
        debug_merge_point(1, 1, 'initialize at LOAD_CONST')
        debug_merge_point(1, 1, 'initialize at STORE_INSTANCE_VAR')
        debug_merge_point(1, 1, 'initialize at DISCARD_TOP')
        debug_merge_point(1, 1, 'initialize at LOAD_SELF')
        debug_merge_point(1, 1, 'initialize at LOAD_CONST')
        debug_merge_point(1, 1, 'initialize at STORE_INSTANCE_VAR')
        debug_merge_point(1, 1, 'initialize at DISCARD_TOP')
        debug_merge_point(1, 1, 'initialize at LOAD_SELF')
        debug_merge_point(1, 1, 'initialize at LOAD_CONST')
        debug_merge_point(1, 1, 'initialize at STORE_INSTANCE_VAR')
        debug_merge_point(1, 1, 'initialize at RETURN')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p48 = force_token()
        i49 = int_add(i41, 1)
        debug_merge_point(0, 0, '<main> at STORE_DEREF')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p24, 58, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p3, p4, p5, p7, p10, i49, p19, p22, p24, p30, descr=TargetToken(4310782288))
        """)

    def test_unboxed_int_storage(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        @i = 0
        while @i < 10000
          @i += 1
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p7, p10, f39, p20, p31, p26, descr=TargetToken(4310773744))
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        i42 = convert_float_bytes_to_longlong(f39)
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p20, 23, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x100ff6bd8>)
        p43 = force_token()
        i44 = int_lt(i42, 10000)
        guard_true(i44, descr=<Guard0x100ff6b60>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at DUP_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p45 = force_token()
        i46 = int_add(i42, 1)
        debug_merge_point(0, 0, '<main> at STORE_INSTANCE_VAR')
        f47 = convert_longlong_bytes_to_float(i46)
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        setfield_gc(p20, 39, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setarrayitem_gc(p26, 0, f47, descr=<ArrayF 8>)
        i48 = arraylen_gc(p26, descr=<ArrayF 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p10, f47, p20, p31, p26, descr=TargetToken(4310773744))
        """)

    def test_unboxed_float_storage(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        @data = 0.0
        while @data < 10000.0
          @data += 1.0
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p7, p10, p20, f37, p30, p26, descr=TargetToken(4310773744))
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p20, 23, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x100ff1d30>)
        p40 = force_token()
        i41 = float_lt(f37, 10000.000000)
        guard_true(i41, descr=<Guard0x100ff1cb8>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        debug_merge_point(0, 0, '<main> at DUP_TOP')
        debug_merge_point(0, 0, '<main> at LOAD_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p42 = force_token()
        f43 = float_add(f37, 1.000000)
        debug_merge_point(0, 0, '<main> at STORE_INSTANCE_VAR')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_SELF')
        setfield_gc(p20, 39, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setarrayitem_gc(p26, 0, f43, descr=<ArrayF 8>)
        i44 = arraylen_gc(p26, descr=<ArrayF 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p10, p20, f43, p30, p26, descr=TargetToken(4310773744))
        """)
