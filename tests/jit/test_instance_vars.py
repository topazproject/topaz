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
        label(p0, p1, p3, p4, p6, p9, i41, p18, p21, p23, p30, p29, descr=TargetToken(4323634304))
        debug_merge_point(0, 0, '<main> at LOAD_DEREF')
        debug_merge_point(0, 0, '<main> at LOAD_CONST')
        debug_merge_point(0, 0, '<main> at SEND')
        setfield_gc(p23, 34, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        guard_not_invalidated(descr=<Guard0x101c0dcb8>)
        p43 = force_token()
        i44 = int_lt(i41, 10000)
        guard_true(i44, descr=<Guard0x101c0dbc8>)
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
        setfield_gc(p23, 58, descr=<FieldS topaz.executioncontext.ExecutionContext.inst_last_instr 24>)
        jump(p0, p1, p3, p4, p6, p9, i49, p18, p21, p23, p30, p29, descr=TargetToken(4323634304))
        """)
