from rupypy import consts
from rupypy.bytecode import Bytecode


class BaseSymbolTable(object):
    FREEVAR = 0
    CELLVAR = 1

    def __init__(self):
        self.subscopes = {}
        self.locals = {}
        self.cells = {}

        self.local_numbers = {}
        self.cell_numbers = {}

    def add_subscope(self, node, symtable):
        self.subscopes[node] = symtable

    def get_subscope(self, node):
        return self.subscopes[node]

    def declare_local(self, name):
        if name not in self.locals:
            self.locals[name] = None

    def is_defined(self, name):
        return self.is_local(name) or self.is_cell(name)

    def is_local(self, name):
        return name in self.locals

    def get_local_num(self, name):
        if name not in self.local_numbers:
            self.local_numbers[name] = len(self.local_numbers)
        return self.local_numbers[name]

    def is_cell(self, name):
        return name in self.cells

    def get_cell_num(self, name):
        if name not in self.cell_numbers:
            self.cell_numbers[name] = len(self.cell_numbers)
        return self.cell_numbers[name]

class SymbolTable(BaseSymbolTable):
    def declare_write(self, name):
        if not self.is_defined(name):
            self.declare_local(name)

    def declare_read(self, name):
        pass

    def upgrade_to_closure(self, name):
        del self.locals[name]
        self.cells[name] = self.CELLVAR


class BlockSymbolTable(BaseSymbolTable):
    def __init__(self, parent_symtable):
        BaseSymbolTable.__init__(self)
        self.parent_symtable = parent_symtable

    def declare_read(self, name):
        if (name not in self.locals and name not in self.cells and
            self.parent_symtable.is_defined(name)):

            self.cells[name] = self.FREEVAR
            self.parent_symtable.upgrade_to_closure(name)

    def declare_write(self, name):
        if name not in self.locals and name not in self.cells:
            if self.parent_symtable.is_defined(name):
                self.cells[name] = self.FREEVAR
                self.parent_symtable.upgrade_to_closure(name)
            else:
                self.declare_local(name)

    def is_defined(self, name):
        return BaseSymbolTable.is_defined(self, name) or self.parent_symtable.is_defined(name)

    def upgrade_to_closure(self, name):
        if self.is_local(name):
            del self.locals[name]
            self.cells[name] = self.CELLVAR
        else:
            self.parent_symtable.upgrade_to_closure(name)
            self.cells[name] = self.FREEVAR


class CompilerContext(object):
    def __init__(self, space, symtable):
        self.space = space
        self.symtable = symtable
        self.data = []
        self.consts = []
        self.const_positions = {}

    def create_bytecode(self, code_name, args):
        bc = "".join(self.data)
        locs = [None] * len(self.symtable.local_numbers)
        for name, pos in self.symtable.local_numbers.iteritems():
            locs[pos] = name

        cellvars = []
        freevars = []

        cells = [None] * len(self.symtable.cell_numbers)
        for name, pos in self.symtable.cell_numbers.iteritems():
            cells[pos] = name

        for name in cells:
            kind = self.symtable.cells[name]
            if kind == self.symtable.CELLVAR:
                cellvars.append(name)
            elif kind == self.symtable.FREEVAR:
                freevars.append(name)
            else:
                assert False

        return Bytecode(
            code_name,
            bc,
            self.count_stackdepth(bc),
            self.consts[:],
            args,
            locs,
            cellvars,
            freevars,
        )

    def count_stackdepth(self, bc):
        i = 0
        current_stackdepth = max_stackdepth = 0
        while i < len(bc):
            c = ord(bc[i])
            i += 1
            stack_effect = consts.BYTECODE_STACK_EFFECT[c]
            if stack_effect == consts.SEND_EFFECT:
                stack_effect = -ord(bc[i+1])
            elif stack_effect == consts.ARRAY_EFFECT:
                stack_effect = -ord(bc[i]) + 1
            elif stack_effect == consts.BLOCK_EFFECT:
                stack_effect = -ord(bc[i])
            i += consts.BYTECODE_NUM_ARGS[c]
            current_stackdepth += stack_effect
            max_stackdepth = max(max_stackdepth, current_stackdepth)
        return max_stackdepth

    def emit(self, c, arg0=-1, arg1=-1):
        self.data.append(chr(c))
        if arg0 != -1:
            self.data.append(chr(arg0))
        if arg1 != -1:
            self.data.append(chr(arg1))

    def get_pos(self):
        return len(self.data)

    def patch_jump(self, pos):
        self.data[pos + 1] = chr(len(self.data))

    def create_const(self, w_obj):
        if w_obj not in self.const_positions:
            self.const_positions[w_obj] = len(self.consts)
            self.consts.append(w_obj)
        return self.const_positions[w_obj]

    def create_int_const(self, intvalue):
        return self.create_const(self.space.newint(intvalue))

    def create_float_const(self, floatvalue):
        return self.create_const(self.space.newfloat(floatvalue))

    def create_symbol_const(self, symbol):
        return self.create_const(self.space.newsymbol(symbol))

    def create_string_const(self, strvalue):
        return self.create_const(self.space.newstr_fromstr(strvalue))
