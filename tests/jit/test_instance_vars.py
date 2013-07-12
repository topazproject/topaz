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

    def test_unboxed_float_storage(self, topaz, tmpdir):
        traces = self.run(topaz, tmpdir, """
        class A
          attr_accessor :data
          def initialize
            @data = 0.0
          end
        end
        a = A.new
        while a.data < 10000.0
            a.data += 1.0
        end
        """)
        self.assert_matches(traces[0].loop, """
        label(p0, p1, p3, p4, p5, p6, p7, p10, p13, p21, p24, p26, f44, p37, p34, descr=TargetToken(4310773744))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p26, 37, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x100ffc278>)
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p46 = force_token()
        setfield_gc(p26, 45, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        i47 = float_lt(f44, 10000.000000)
        guard_true(i47, descr=<Guard0x100ffc200>)
        debug_merge_point(0, 0, '<main> at JUMP_IF_FALSE')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at DUP_TOP')
        debug_merge_point(0, 0, '<main> at SEND')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        p48 = force_token()
        f49 = float_add(f44, 1.000000)
        debug_merge_point(0, 0, '<main> at SEND')
        debug_merge_point(0, 0, '<main> at DISCARD_TOP')
        debug_merge_point(0, 0, '<main> at JUMP')
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        setfield_gc(p26, 70, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        setarrayitem_gc(p34, 0, f49, descr=<ArrayF 8>)
        i50 = arraylen_gc(p34, descr=<ArrayF 8>)
        jump(p0, p1, p3, p4, p5, p6, p7, p10, p13, p21, p24, p26, f49, p37, p34, descr=TargetToken(4310773744))
        """)
