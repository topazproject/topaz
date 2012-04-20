from rupypy import consts
from rupypy.bytecode import Bytecode


class BaseSymbolTable(object):
    def __init__(self):
        self.subscopes = {}
        self.locals = {}
        self.local_counter = 0
        self.cells = {}

    def add_subscope(self, node, symtable):
        self.subscopes[node] = symtable

    def get_subscope(self, node):
        return self.subscopes[node]

    def declare_local(self, name):
        if name not in self.locals:
            self.locals[name] = self.local_counter
            self.local_counter += 1

    def is_local(self, name):
        return name in self.locals

    def get_local_num(self, name):
        return self.locals[name]

    def upgrade_to_closure(self, name):
        del self.locals[name]
        self.cells[name] = len(self.cells)

    def is_cell(self, name):
        return name in self.cells

    def get_cell_num(self, name):
        return self.cells[name]

class SymbolTable(BaseSymbolTable):
    def declare_write(self, name):
        self.declare_local(name)

    def declare_read(self, name):
        pass

    def defined(self, name):
        return self.is_local(name)

class BlockSymbolTable(BaseSymbolTable):
    def __init__(self, parent_symtable):
        BaseSymbolTable.__init__(self)
        self.parent_symtable = parent_symtable

    def declare_read(self, name):
        if  (name not in self.locals and name not in self.cells and
            self.parent_symtable.defined(name)):

            self.cells[name] = len(self.cells)
            self.parent_symtable.upgrade_to_closure(name)

    def declare_write(self, name):
        if name not in self.locals and name not in self.cells:
            if self.parent_symtable.defined(name):
                self.cells[name] = len(self.cells)
                self.parent_symtable.upgrade_to_closure(name)
            else:
                self.declare_local(name)


class CompilerContext(object):
    def __init__(self, space, symtable):
        self.space = space
        self.symtable = symtable
        self.data = []
        self.consts = []
        self.const_positions = {}

    def create_bytecode(self, args):
        bc = "".join(self.data)
        locs = [None] * self.symtable.local_counter
        for name, pos in self.symtable.locals.iteritems():
            locs[pos] = name
        cells = [None] * len(self.symtable.cells)
        for name, pos in self.symtable.cells.iteritems():
            cells[pos] = name
        return Bytecode(bc, self.count_stackdepth(bc), self.consts[:], args, locs, cells)

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
