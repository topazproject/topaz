from topaz.objects.objectobject import W_BaseObject


class W_BlockObject(W_BaseObject):
    def __init__(self, bytecode, w_self, lexical_scope, cells, block,
                 parent_interp, regexp_match_cell):
        self.bytecode = bytecode
        self.w_self = w_self
        self.lexical_scope = lexical_scope
        self.cells = cells
        self.block = block
        self.parent_interp = parent_interp
        self.regexp_match_cell = regexp_match_cell

    def copy(self, bytecode=None, w_self=None, lexical_scope=None, cells=None,
             block=None, parent_interp=None):
        return W_BlockObject(
            bytecode or self.bytecode,
            w_self or self.w_self,
            lexical_scope or self.lexical_scope,
            cells or self.cells,
            block or self.block,
            parent_interp or self.parent_interp,
            self.regexp_match_cell,
        )
