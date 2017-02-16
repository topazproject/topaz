from topaz.astcompiler import SymbolTable
from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_BindingObject(W_Object):
    classdef = ClassDef("Binding", W_Object.classdef)
    _immutable_fields_ = ["names[*]", "cells[*]", "w_self", "lexical_scope"]

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
        frame = space.create_frame(bc, w_self=self.w_self, lexical_scope=self.lexical_scope)
        for idx, cell in enumerate(self.cells):
            frame.cells[idx + len(bc.cellvars)] = cell
        with space.getexecutioncontext().visit_frame(frame):
            return space.execute_frame(frame, bc)
