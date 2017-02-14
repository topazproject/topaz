from topaz import consts
from topaz.objects.codeobject import W_CodeObject


class BaseSymbolTable(object):
    FREEVAR = 0
    CELLVAR = 1

    NORMAL_ARG = 0
    SPLAT_ARG = 1
    KW_ARG = 2
    BLOCK_ARG = 3

    def __init__(self, parent_symtable=None):
        self.parent_symtable = parent_symtable
        self.subscopes = {}
        self.cells = {}
        self.arguments = []

        self.cell_numbers = {}

    def add_subscope(self, node, symtable):
        self.subscopes[node] = symtable

    def get_subscope(self, node):
        return self.subscopes[node]

    def declare_argument(self, name, tp=NORMAL_ARG):
        self.arguments.append((name, tp))
        self.declare_local(name)

    def declare_local(self, name):
        self.cells[name] = self.CELLVAR

    def is_defined(self, name):
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
        pass


class BlockSymbolTable(BaseSymbolTable):
    def declare_read(self, name):
        if name not in self.cells and self.parent_symtable.is_defined(name):
            self.cells[name] = self.FREEVAR
            self.parent_symtable.upgrade_to_closure(name)

    def declare_write(self, name):
        if name not in self.cells:
            if self.parent_symtable.is_defined(name):
                self.cells[name] = self.FREEVAR
                self.parent_symtable.upgrade_to_closure(name)
            else:
                self.declare_local(name)

    def is_defined(self, name):
        return BaseSymbolTable.is_defined(self, name) or self.parent_symtable.is_defined(name)

    def upgrade_to_closure(self, name):
        if name not in self.cells:
            self.parent_symtable.upgrade_to_closure(name)
            self.cells[name] = self.FREEVAR


class SharedScopeSymbolTable(BlockSymbolTable):
    def declare_write(self, name):
        self.parent_symtable.declare_write(name)
        BlockSymbolTable.declare_write(self, name)


class CompilerContext(object):
    F_BLOCK_LOOP = 0
    F_BLOCK_FINALLY = 1
    F_BLOCK_FINALLY_END = 2

    def __init__(self, space, code_name, symtable, filepath):
        self.space = space
        self.code_name = code_name
        self.symtable = symtable
        self.filepath = filepath
        self.consts = []
        self.const_positions = {}
        self.current_lineno = -1
        self.last_lineno = -1

        self.current_block = self.first_block = self.new_block()
        self.frame_blocks = []

    def create_bytecode(self, lineno=-1, args=None, defaults=None,
                        first_default_arg=None, splat_arg=None, kwargs=None,
                        kw_defaults=None, kwrest_arg=None, block_arg=None):
        if args is None:
            args = []
        if defaults is None:
            defaults = []
        if kwargs is None:
            kwargs = []
        if kw_defaults is None:
            kw_defaults = []

        cellvars = []
        freevars = []

        # Make sure that any cell vars have a number.
        for name in self.symtable.cells:
            if name not in self.symtable.cell_numbers:
                self.symtable.get_cell_num(name)

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

        blocks = self.first_block.post_order()
        code, lineno_table = self.get_code_lineno_table(blocks)
        depth = self.count_stackdepth(blocks)
        for default in defaults:
            depth = max(depth, default.max_stackdepth)
        for kw_default in kw_defaults:
            depth = max(depth, kw_default.max_stackdepth)
        return W_CodeObject(
            self.code_name,
            self.filepath,
            lineno,
            code,
            depth,
            self.consts[:],
            args,
            splat_arg,
            kwargs,
            kwrest_arg,
            block_arg,
            defaults,
            first_default_arg,
            kw_defaults,
            cellvars,
            freevars,
            lineno_table,
        )

    def get_code_lineno_table(self, blocks):
        offsets = {}
        code_size = 0
        for block in blocks:
            offsets[block] = code_size
            code = []
            linenos = []
            block.get_code(code, linenos)
            code_size += len(code)
        for block in blocks:
            block.patch_locs(offsets)

        code = []
        linenos = []
        for block in blocks:
            block.get_code(code, linenos)
        return "".join(code), linenos

    def count_stackdepth(self, blocks):
        for b in blocks:
            b.marked = False
            b.initial_depth = -1
        return self._count_stackdepth(blocks[0], 0, 0)

    def _count_stackdepth(self, block, depth, max_depth):
        if block.marked or block.initial_depth >= depth:
            return max_depth

        block.marked = True
        block.initial_depth = depth

        for instr in block.instrs:
            depth += self._instr_stack_effect(instr)
            max_depth = max(max_depth, depth)
            if instr.has_jump():
                target_depth = depth
                jump_op = instr.opcode
                if jump_op in [consts.SETUP_FINALLY, consts.SETUP_EXCEPT]:
                    target_depth += 3
                    max_depth = max(max_depth, target_depth)
                max_depth = self._count_stackdepth(instr.jump, target_depth, max_depth)
        if block.next_block is not None:
            max_depth = self._count_stackdepth(block.next_block, depth, max_depth)
        block.marked = False
        return max_depth

    def _instr_stack_effect(self, instr):
        stack_effect = consts.BYTECODE_STACK_EFFECT[instr.opcode]
        if stack_effect == consts.SEND_EFFECT:
            stack_effect = -instr.arg1
        elif stack_effect == consts.ARRAY_EFFECT:
            stack_effect = -instr.arg0 + 1
        elif stack_effect == consts.BLOCK_EFFECT:
            stack_effect = -instr.arg0
        elif stack_effect == consts.UNPACK_EFFECT:
            stack_effect = instr.arg0 - 1
        return stack_effect

    def set_lineno(self, lineno):
        return SetLinenoConextManager(self, lineno)

    def enter_frame_block(self, block_type, block):
        return EnterFrameBlockContextManager(self, block_type, block)

    def in_frame_block(self, block_type):
        for t, _ in self.frame_blocks:
            if t == block_type:
                return True
        return False

    def find_frame_block(self, block_type):
        for frame_block in reversed(self.frame_blocks):
            if frame_block[0] == block_type:
                return frame_block[1]
        raise SystemError

    def new_block(self):
        return Block()

    def use_block(self, block):
        self.current_block = block

    def use_next_block(self, block):
        self.current_block.next_block = block
        self.use_block(block)

    def emit(self, opcode, arg0=-1, arg1=-1):
        num_args = 0
        if arg0 != -1:
            num_args += 1
            if arg1 != -1:
                num_args += 1
        assert num_args == consts.BYTECODE_NUM_ARGS[opcode]
        instr = Instruction(opcode, arg0, arg1, self.current_lineno)
        self.current_block.instrs.append(instr)
        self.last_lineno = self.current_lineno

    def emit_jump(self, opcode, target):
        instr = Instruction(opcode, 0, -1, self.current_lineno)
        instr.jump = target
        self.current_block.instrs.append(instr)

    def get_subctx(self, name, node):
        subscope = self.symtable.get_subscope(node)
        return CompilerContext(self.space, name, subscope, self.filepath)

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


class Block(object):
    def __init__(self):
        self.instrs = []
        self.marked = False
        self.next_block = None

    def post_order(self):
        blocks = []
        self._post_order(blocks)
        blocks.reverse()
        return blocks

    def _post_order(self, blocks):
        if self.marked:
            return
        self.marked = True
        if self.next_block is not None:
            self.next_block._post_order(blocks)
        for instr in self.instrs:
            if instr.has_jump():
                instr.jump._post_order(blocks)
        blocks.append(self)

    def patch_locs(self, offsets):
        for instr in self.instrs:
            instr.patch_loc(offsets)

    def get_code(self, code, linenos):
        for instr in self.instrs:
            instr.emit(code, linenos)
        return "".join(code)


class Instruction(object):
    def __init__(self, opcode, arg0, arg1, lineno):
        assert arg0 < 1 << 16
        assert arg1 < 1 << 16
        self.opcode = opcode
        self.arg0 = arg0
        self.arg1 = arg1
        self.lineno = lineno
        self.jump = None

    def emit(self, code, linenos):
        code.append(chr(self.opcode))
        linenos.append(self.lineno)
        if self.arg0 != -1:
            code.append(chr(self.arg0 & 0xFF))
            code.append(chr(self.arg0 >> 8))
            linenos.append(self.lineno)
            linenos.append(self.lineno)
        if self.arg1 != -1:
            code.append(chr(self.arg1 & 0xFF))
            code.append(chr(self.arg1 >> 8))
            linenos.append(self.lineno)
            linenos.append(self.lineno)

    def has_jump(self):
        return self.jump is not None

    def patch_loc(self, offsets):
        if self.has_jump():
            self.arg0 = offsets[self.jump]


class SetLinenoConextManager(object):
    def __init__(self, ctx, lineno):
        self.ctx = ctx
        self.lineno = lineno

    def __enter__(self):
        self.orig_lineno = self.ctx.current_lineno
        self.ctx.current_lineno = self.lineno

    def __exit__(self, exc_type, exc_value, tb):
        self.ctx.current_lineno = self.orig_lineno


class EnterFrameBlockContextManager(object):
    def __init__(self, ctx, block_type, block):
        self.ctx = ctx
        self.block_type = block_type
        self.block = block

    def __enter__(self):
        self.ctx.frame_blocks.append((self.block_type, self.block))

    def __exit__(self, exc_type, exc_value, tb):
        block_type, block = self.ctx.frame_blocks.pop()
        assert block_type == self.block_type
        assert block is self.block


class CompilerError(Exception):
    def __init__(self, msg=None):
        self.msg = "" if msg is None else msg
