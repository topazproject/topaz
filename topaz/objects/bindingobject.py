from rpython.rlib import jit

from topaz.astcompiler import SymbolTable
from topaz.closure import ClosureCell
from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_BindingObject(W_Object):
    classdef = ClassDef("Binding", W_Object.classdef)
    _immutable_fields_ = ["names[*]?", "cells[*]?", "w_self", "lexical_scope"]

    def __init__(self, space, names, cells, w_self, lexical_scope):
        W_Object.__init__(self, space)
        self.names = names
        self.cells = cells
        self.w_self = w_self
        self.lexical_scope = lexical_scope

    classdef.undefine_allocator()

    @classdef.method("eval", source="str")
    def method_eval(self, space, source):
        symtable = SymbolTable()
        for name in self.names:
            symtable.cells[name] = symtable.FREEVAR
        bc = space.compile(source, "(eval)", symtable=symtable)
        frame = space.create_frame(
            bc, w_self=self.w_self, lexical_scope=self.lexical_scope)
        for idx, cell in enumerate(self.cells):
            frame.cells[idx + len(bc.cellvars)] = cell
        with space.getexecutioncontext().visit_frame(frame):
            return space.execute_frame(frame, bc)

    @classdef.method("local_variable_defined?", key="symbol")
    def method_local_variable_definedp(self, space, key):
        return space.newbool(key in self.names)

    @jit.unroll_safe
    @classdef.method("local_variable_get", key="symbol")
    def method_local_variable_get(self, space, key):
        for idx, name in enumerate(self.names):
            if name == key:
                return self.cells[idx].get(space, None, 0)
        return space.w_nil

    @jit.unroll_safe
    @classdef.method("local_variable_set", key="symbol")
    def method_local_variable_set(self, space, key, w_value):
        for idx, name in enumerate(self.names):
            if name == key:
                self.cells[idx].set(space, None, 0, w_value)
                return
        self.names.append(key)
        self.cells.append(ClosureCell(w_value))

    @classdef.method("local_variables")
    def method_local_variables(self, space):
        return space.newarray([space.newstr_fromstr(n) for n in self.names])

    @classdef.method("receiver")
    def method_receiver(self, space):
        return self.w_self
