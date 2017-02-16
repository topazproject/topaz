from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_ProcObject(W_Object):
    classdef = ClassDef("Proc", W_Object.classdef)
    _immutable_fields_ = [
        "bytecode", "w_self", "lexical_scope", "cells[*]",
        "block", "parent_interp", "top_parent_interp",
        "regexp_match_cell", "is_lambda"]

    def __init__(self, space, bytecode, w_self, lexical_scope, cells, block,
                 parent_interp, top_parent_interp, regexp_match_cell,
                 is_lambda):
        W_Object.__init__(self, space)
        self.bytecode = bytecode
        self.w_self = w_self
        self.lexical_scope = lexical_scope
        self.cells = cells
        self.block = block
        self.parent_interp = parent_interp
        self.top_parent_interp = top_parent_interp
        self.regexp_match_cell = regexp_match_cell
        self.is_lambda = is_lambda

    def copy(self, space, w_self=None, lexical_scope=None, is_lambda=False):
        return W_ProcObject(
            space, self.bytecode,
            w_self or self.w_self,
            lexical_scope or self.lexical_scope,
            self.cells, self.block, self.parent_interp, self.top_parent_interp,
            self.regexp_match_cell,
            is_lambda or self.is_lambda
        )

    @classdef.singleton_method("new")
    def method_new(self, space, block):
        if block is None:
            block = space.getexecutioncontext().gettoprubyframe().block
        if block is None:
            raise space.error(space.w_ArgumentError, "tried to create Proc object without a block")
        return block.copy(space)

    method_allocate = classdef.undefine_allocator()

    @classdef.method("yield")
    @classdef.method("===")
    @classdef.method("[]")
    @classdef.method("call")
    def method_call(self, space, args_w, block):
        from topaz.interpreter import RaiseReturn, RaiseBreak

        try:
            return space.invoke_block(self, args_w, block_arg=block)
        except RaiseReturn as e:
            if self.is_lambda:
                return e.w_value
            else:
                raise
        except RaiseBreak as e:
            if self.is_lambda:
                return e.w_value
            else:
                raise space.error(space.w_LocalJumpError, "break from proc-closure")

    @classdef.method("lambda?")
    def method_lambda(self, space):
        return space.newbool(self.is_lambda)

    @classdef.method("arity")
    def method_arity(self, space):
        return space.newint(self.bytecode.arity(negative_defaults=self.is_lambda))

    @classdef.method("binding")
    def method_binding(self, space):
        return space.newbinding_fromblock(self)

    @classdef.method("source_location")
    def method_source_location(self, space):
        return space.newarray([
            space.newstr_fromstr(self.bytecode.filepath),
            space.newint(self.bytecode.lineno)
        ])
