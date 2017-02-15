from __future__ import absolute_import

from rpython.rlib.objectmodel import we_are_translated

from topaz import consts
from topaz.astcompiler import CompilerContext, BlockSymbolTable, CompilerError
from topaz.utils.regexp import RegexpError


class BaseNode(object):
    _attrs_ = []

    def __eq__(self, other):
        if not isinstance(other, BaseNode):
            return NotImplemented
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def compile(self, ctx):
        if we_are_translated():
            raise NotImplementedError
        else:
            raise NotImplementedError(type(self).__name__)

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class Node(BaseNode):
    _attrs_ = ["lineno"]

    def __init__(self, lineno):
        self.lineno = lineno


class Main(Node):
    def __init__(self, block):
        self.block = block

    def compile(self, ctx):
        self.block.compile(ctx)
        ctx.emit(consts.RETURN)


class Block(Node):
    def __init__(self, stmts):
        # The last item shouldn't be popped.
        node = stmts[-1]
        assert isinstance(node, BaseStatement)
        node.dont_pop = True

        self.stmts = stmts

    def compile(self, ctx):
        for idx, stmt in enumerate(self.stmts):
            stmt.compile(ctx)

    def compile_defined(self, ctx):
        self.stmts[-1].compile_defined(ctx)


class BaseStatement(Node):
    dont_pop = False


class Statement(BaseStatement):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        if not self.dont_pop:
            with ctx.set_lineno(ctx.last_lineno):
                ctx.emit(consts.DISCARD_TOP)

    def compile_defined(self, ctx):
        self.expr.compile_defined(ctx)


class If(Node):
    def __init__(self, cond, body, elsebody):
        self.cond = cond
        self.body = body
        self.elsebody = elsebody

    def compile(self, ctx):
        end = ctx.new_block()
        otherwise = ctx.new_block()
        self.cond.compile(ctx)
        ctx.emit_jump(consts.JUMP_IF_FALSE, otherwise)
        self.body.compile(ctx)
        ctx.emit_jump(consts.JUMP, end)
        ctx.use_next_block(otherwise)
        self.elsebody.compile(ctx)
        ctx.use_next_block(end)


class BaseLoop(Node):
    def __init__(self, cond, body, post_check=False):
        self.cond = cond
        self.body = body
        self.post_check = post_check

    def compile(self, ctx):
        anchor = ctx.new_block()
        end = ctx.new_block()
        loop = ctx.new_block()

        if self.post_check:
            self.body.compile(ctx)
            ctx.emit(consts.DISCARD_TOP)
        ctx.emit_jump(consts.SETUP_LOOP, end)
        with ctx.enter_frame_block(ctx.F_BLOCK_LOOP, loop):
            ctx.use_next_block(loop)
            self.cond.compile(ctx)
            ctx.emit_jump(self.cond_instr, anchor)

            self.body.compile(ctx)
            ctx.emit(consts.DISCARD_TOP)
            ctx.emit_jump(consts.JUMP, loop)

            ctx.use_next_block(anchor)
            ctx.emit(consts.POP_BLOCK)
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))
        ctx.use_next_block(end)


class While(BaseLoop):
    cond_instr = consts.JUMP_IF_FALSE


class Until(BaseLoop):
    cond_instr = consts.JUMP_IF_TRUE


class Next(BaseStatement):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        if ctx.in_frame_block(ctx.F_BLOCK_LOOP):
            block = ctx.find_frame_block(ctx.F_BLOCK_LOOP)
            ctx.emit_jump(consts.CONTINUE_LOOP, block)
        elif isinstance(ctx.symtable, BlockSymbolTable):
            ctx.emit(consts.RETURN)
        else:
            raise CompilerError("void value expression")


class Break(BaseStatement):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        if ctx.in_frame_block(ctx.F_BLOCK_LOOP):
            ctx.emit(consts.BREAK_LOOP)
        elif isinstance(ctx.symtable, BlockSymbolTable):
            ctx.emit(consts.RAISE_BREAK)
        else:
            raise CompilerError("void value expression")


class TryExcept(Node):
    def __init__(self, body, except_handlers, else_body):
        self.body = body
        self.except_handlers = except_handlers
        self.else_body = else_body

    def compile(self, ctx):
        exc = ctx.new_block()
        else_block = ctx.new_block()
        end = ctx.new_block()
        if self.except_handlers:
            ctx.emit_jump(consts.SETUP_EXCEPT, exc)
        ctx.use_next_block(ctx.new_block())
        self.body.compile(ctx)
        if self.except_handlers:
            ctx.emit(consts.POP_BLOCK)
        ctx.emit_jump(consts.JUMP, else_block)
        ctx.use_next_block(exc)

        for handler in self.except_handlers:
            assert isinstance(handler, ExceptHandler)
            next_except = ctx.new_block()
            handle_block = ctx.new_block()

            if handler.exceptions:
                for exception in handler.exceptions:
                    next_handle = ctx.new_block()
                    ctx.emit(consts.DUP_TOP)
                    exception.compile(ctx)
                    ctx.emit(consts.ROT_TWO)
                    ctx.emit(consts.SEND, ctx.create_symbol_const("==="), 1)
                    ctx.emit_jump(consts.JUMP_IF_TRUE, handle_block)
                    ctx.use_next_block(next_handle)
                ctx.emit_jump(consts.JUMP, next_except)
            ctx.use_next_block(handle_block)
            if handler.target:
                elems = handler.target.compile_receiver(ctx)
                if elems == 1:
                    ctx.emit(consts.ROT_TWO)
                elif elems == 2:
                    ctx.emit(consts.ROT_THREE)
                    ctx.emit(consts.ROT_THREE)
                handler.target.compile_store(ctx)
            ctx.emit(consts.DISCARD_TOP)
            ctx.emit(consts.DISCARD_TOP)
            handler.body.compile(ctx)
            ctx.emit_jump(consts.JUMP, end)
            ctx.use_next_block(next_except)

        if self.except_handlers:
            ctx.emit(consts.END_FINALLY)
        ctx.use_next_block(else_block)
        self.else_body.compile(ctx)
        ctx.emit(consts.DISCARD_TOP)
        ctx.use_next_block(end)


class ExceptHandler(Node):
    def __init__(self, exceptions, target, body):
        self.exceptions = exceptions
        self.target = target
        self.body = body


class TryFinally(Node):
    def __init__(self, body, finally_body):
        self.body = body
        self.finally_body = finally_body

    def compile(self, ctx):
        end = ctx.new_block()
        ctx.emit_jump(consts.SETUP_FINALLY, end)
        body = ctx.new_block()
        ctx.use_next_block(body)
        with ctx.enter_frame_block(ctx.F_BLOCK_FINALLY, body):
            self.body.compile(ctx)
            ctx.emit(consts.POP_BLOCK)
        # Put a None on the stack where an exception would be.
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))
        ctx.use_next_block(end)
        with ctx.enter_frame_block(ctx.F_BLOCK_FINALLY_END, end):
            self.finally_body.compile(ctx)
            ctx.emit(consts.DISCARD_TOP)
            ctx.emit(consts.END_FINALLY)


class BaseModule(Node):
    def __init__(self, scope, name, body):
        self.scope = scope
        self.name = name
        self.body = body

    def compile_body(self, ctx, ctxname):
        body_ctx = ctx.get_subctx(ctxname, self)
        self.body.compile(body_ctx)
        body_ctx.emit(consts.RETURN)
        bytecode = body_ctx.create_bytecode()

        ctx.emit(consts.LOAD_CONST, ctx.create_const(bytecode))
        ctx.emit(consts.EVALUATE_MODULE)


class Class(BaseModule):
    def __init__(self, scope, name, superclass, body):
        BaseModule.__init__(self, scope, name, body)
        self.superclass = superclass

    def compile(self, ctx):
        if self.scope is not None:
            self.scope.compile(ctx)
        else:
            ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_object))
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        if self.superclass is None:
            ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))
        else:
            self.superclass.compile(ctx)
        ctx.emit(consts.BUILD_CLASS)
        self.compile_body(ctx, "<class:%s>" % self.name)


class SingletonClass(BaseModule):
    def __init__(self, value, body, lineno):
        Node.__init__(self, lineno)
        self.value = value
        self.body = body

    def compile(self, ctx):
        with ctx.set_lineno(self.lineno):
            self.value.compile(ctx)
            ctx.emit(consts.LOAD_SINGLETON_CLASS)
            self.compile_body(ctx, "singletonclass")


class Module(BaseModule):
    def compile(self, ctx):
        if self.scope is not None:
            self.scope.compile(ctx)
        else:
            ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_object))
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        ctx.emit(consts.BUILD_MODULE)
        self.compile_body(ctx, "<module:%s>" % self.name)


class AbstractCallable(Node):
    def get_code_name(self, ctx):
        raise NotImplementedError("Abstract class")

    def post_process_ctx(self, ctx, code_ctx):
        raise NotImplementedError("Abstract class")

    def compile_bytecode(self, ctx, code_ctx, args, splat_arg, post_args, kwargs, kwrest_arg, block_arg, body):
        ctxname = self.get_code_name(ctx)
        arg_names = []
        arg_defaults = []
        kw_arg_names = []
        kw_defaults = []
        first_default_arg = None
        for arg in args:
            assert isinstance(arg, Argument)
            if arg.defl is None:
                arg_names.append(arg.name)
                code_ctx.symtable.get_cell_num(arg.name)
        for arg in args:
            assert isinstance(arg, Argument)
            if arg.defl is not None:
                arg_names.append(arg.name)
                code_ctx.symtable.get_cell_num(arg.name)
                if first_default_arg is None:
                    first_default_arg = arg.name
                arg_ctx = CompilerContext(ctx.space, ctxname, code_ctx.symtable, ctx.filepath)
                arg.defl.compile(arg_ctx)
                arg_ctx.emit(consts.RETURN)
                bc = arg_ctx.create_bytecode()
                arg_defaults.append(bc)
        if splat_arg is not None:
            code_ctx.symtable.get_cell_num(splat_arg)
        for arg in post_args:
            assert isinstance(arg, Argument)
            arg_names.append(arg.name)
            code_ctx.symtable.get_cell_num(arg.name)
            assert arg.defl is None
        # this sorting of kwargs with defaults first is important for arg
        # handling in frame.py
        for arg in kwargs:
            assert isinstance(arg, Argument)
            if arg.defl is not None:
                code_ctx.symtable.get_cell_num(arg.name)
                arg_ctx = CompilerContext(ctx.space, ctxname, code_ctx.symtable, ctx.filepath)
                arg.defl.compile(arg_ctx)
                arg_ctx.emit(consts.RETURN)
                bc = arg_ctx.create_bytecode()
                kw_defaults.append(bc)
        for arg in kwargs:
            assert isinstance(arg, Argument)
            code_ctx.symtable.get_cell_num(arg.name)
            kw_arg_names.append(arg.name)
        if kwrest_arg is not None:
            code_ctx.symtable.get_cell_num(kwrest_arg)
        if block_arg is not None:
            code_ctx.symtable.get_cell_num(block_arg)
        self.post_process_ctx(ctx, code_ctx)
        body.compile(code_ctx)
        code_ctx.emit(consts.RETURN)

        return code_ctx.create_bytecode(
            lineno=self.lineno,
            args=arg_names,
            defaults=arg_defaults,
            first_default_arg=first_default_arg,
            splat_arg=splat_arg,
            kwargs=kw_arg_names,
            kw_defaults=kw_defaults,
            kwrest_arg=kwrest_arg,
            block_arg=block_arg,
        )


class Function(AbstractCallable):
    def __init__(self, lineno, parent, name, args, splat_arg, post_args, kwargs, kwrest_arg, block_arg, body):
        Node.__init__(self, lineno)
        self.parent = parent
        self.name = name
        self.args = args
        self.splat_arg = splat_arg
        self.post_args = post_args
        self.kwargs = kwargs
        self.kwrest_arg = kwrest_arg
        self.block_arg = block_arg
        self.body = body

    def get_code_name(self, ctx):
        return self.name

    def post_process_ctx(self, ctx, code_ctx):
        pass

    def compile(self, ctx):
        code_ctx = ctx.get_subctx(self.name, self)
        bc = self.compile_bytecode(
            ctx, code_ctx,
            self.args, self.splat_arg, self.post_args,
            self.kwargs, self.kwrest_arg, self.block_arg, self.body
        )
        if self.parent is None:
            ctx.emit(consts.LOAD_SCOPE)
        else:
            self.parent.compile(ctx)
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        ctx.emit(consts.LOAD_CONST, ctx.create_const(bc))
        ctx.emit(consts.BUILD_FUNCTION)
        if self.parent is None:
            ctx.emit(consts.DEFINE_FUNCTION)
        else:
            ctx.emit(consts.ATTACH_FUNCTION)


class Argument(Node):
    def __init__(self, name, defl=None):
        self.name = name
        self.defl = defl


class Lambda(Node):
    def __init__(self, block):
        self.block = block

    def compile(self, ctx):
        self.block.compile(ctx)
        ctx.emit(consts.BUILD_LAMBDA)


class Case(Node):
    def __init__(self, cond, whens, elsebody):
        self.cond = cond
        self.whens = whens
        self.elsebody = elsebody

    def compile(self, ctx):
        end = ctx.new_block()

        self.cond.compile(ctx)
        for when in self.whens:
            assert isinstance(when, When)
            with ctx.set_lineno(when.lineno):
                next_when = ctx.new_block()
                when_block = ctx.new_block()

                for expr in when.conds:
                    next_expr = ctx.new_block()
                    ctx.emit(consts.DUP_TOP)
                    expr.compile(ctx)
                    ctx.emit(consts.ROT_TWO)
                    ctx.emit(consts.SEND, ctx.create_symbol_const("==="), 1)
                    ctx.emit_jump(consts.JUMP_IF_TRUE, when_block)
                    ctx.use_next_block(next_expr)
                ctx.emit_jump(consts.JUMP, next_when)
                ctx.use_next_block(when_block)
                ctx.emit(consts.DISCARD_TOP)
                when.block.compile(ctx)
                ctx.emit_jump(consts.JUMP, end)
                ctx.use_next_block(next_when)
        ctx.emit(consts.DISCARD_TOP)
        self.elsebody.compile(ctx)
        ctx.use_next_block(end)


class When(Node):
    def __init__(self, conds, block, lineno):
        Node.__init__(self, lineno)
        self.conds = conds
        self.block = block


class Return(BaseStatement):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        if isinstance(ctx.symtable, BlockSymbolTable):
            ctx.emit(consts.RAISE_RETURN)
        else:
            ctx.emit(consts.RETURN)


class Yield(Node):
    def __init__(self, args, lineno):
        Node.__init__(self, lineno)
        self.args = args

    def compile(self, ctx):
        with ctx.set_lineno(self.lineno):
            if self.is_splat():
                for arg in self.args:
                    arg.compile(ctx)
                    if not isinstance(arg, Splat):
                        ctx.emit(consts.BUILD_ARRAY, 1)
                ctx.emit(consts.YIELD_SPLAT, len(self.args))
            else:
                for arg in self.args:
                    arg.compile(ctx)
                ctx.emit(consts.YIELD, len(self.args))

    def is_splat(self):
        for arg in self.args:
            if isinstance(arg, Splat):
                return True
        return False

    def compile_defined(self, ctx):
        ctx.emit(consts.DEFINED_YIELD)


class Alias(BaseStatement):
    def __init__(self, new_name, old_name, lineno):
        BaseStatement.__init__(self, lineno)
        self.new_name = new_name
        self.old_name = old_name

    def compile(self, ctx):
        Send(
            Scope(self.lineno),
            "alias_method",
            [self.new_name, self.old_name],
            None,
            self.lineno,
        ).compile(ctx)
        if not self.dont_pop:
            ctx.emit(consts.DISCARD_TOP)


class Undef(BaseStatement):
    def __init__(self, undef_list, lineno):
        BaseStatement.__init__(self, lineno)
        self.undef_list = undef_list

    def compile(self, ctx):
        first = True
        for undef in self.undef_list:
            if not first:
                ctx.emit(consts.DISCARD_TOP)
            Send(
                Scope(self.lineno),
                "undef_method",
                [undef],
                None,
                self.lineno
            ).compile(ctx)
        if not self.dont_pop:
            ctx.emit(consts.DISCARD_TOP)


class Defined(Node):
    def __init__(self, node, lineno):
        Node.__init__(self, lineno)
        self.node = node

    def compile(self, ctx):
        self.node.compile_defined(ctx)


class Assignment(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def compile(self, ctx):
        self.target.compile_receiver(ctx)
        self.value.compile(ctx)
        self.target.compile_store(ctx)

    def compile_defined(self, ctx):
        ConstantString("assignment").compile(ctx)


class AugmentedAssignment(Node):
    def __init__(self, oper, target, value):
        self.oper = oper
        self.target = target
        self.value = value

    def compile(self, ctx):
        dup_needed = self.target.compile_receiver(ctx)
        if dup_needed == 1:
            ctx.emit(consts.DUP_TOP)
        elif dup_needed == 2:
            ctx.emit(consts.DUP_TWO)
        self.target.compile_load(ctx)
        self.value.compile(ctx)
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper), 1)
        self.target.compile_store(ctx)

    def compile_defined(self, ctx):
        ConstantString("assignment").compile(ctx)


class OrEqual(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def compile(self, ctx):
        otherwise = ctx.new_block()
        end = ctx.new_block()

        dup_needed = self.target.compile_receiver(ctx)
        if dup_needed == 1:
            ctx.emit(consts.DUP_TOP)
        elif dup_needed == 2:
            ctx.emit(consts.DUP_TWO)
        self.target.compile_load(ctx)
        ctx.emit(consts.DUP_TOP)
        ctx.emit_jump(consts.JUMP_IF_TRUE, end)
        ctx.use_next_block(otherwise)
        ctx.emit(consts.DISCARD_TOP)
        self.value.compile(ctx)
        ctx.use_next_block(end)
        self.target.compile_store(ctx)

    def compile_defined(self, ctx):
        ConstantString("assignment").compile(ctx)


class AndEqual(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def compile(self, ctx):
        otherwise = ctx.new_block()
        end = ctx.new_block()

        dup_needed = self.target.compile_receiver(ctx)
        if dup_needed == 1:
            ctx.emit(consts.DUP_TOP)
        elif dup_needed == 2:
            ctx.emit(consts.DUP_TWO)
        self.target.compile_load(ctx)
        ctx.emit(consts.DUP_TOP)
        ctx.emit_jump(consts.JUMP_IF_FALSE, end)
        ctx.use_next_block(otherwise)
        ctx.emit(consts.DISCARD_TOP)
        self.value.compile(ctx)
        ctx.use_next_block(end)
        self.target.compile_store(ctx)

    def compile_defined(self, ctx):
        ConstantString("assignment").compile(ctx)


class MultiAssignable(Node):
    def __init__(self, targets):
        self.targets = targets

    def splat_index(self):
        for i, node in enumerate(self.targets):
            if isinstance(node, Splat):
                return i
        return -1

    def compile_receiver(self, ctx):
        return 0

    def compile_store(self, ctx):
        ctx.emit(consts.DUP_TOP)
        ctx.emit(consts.COERCE_ARRAY, 0)
        splat_index = self.splat_index()
        if splat_index == -1:
            ctx.emit(consts.UNPACK_SEQUENCE, len(self.targets))
        else:
            ctx.emit(consts.UNPACK_SEQUENCE_SPLAT, len(self.targets), splat_index)
        for target in self.targets:
            elems = target.compile_receiver(ctx)
            if elems == 1:
                ctx.emit(consts.ROT_TWO)
            elif elems == 2:
                ctx.emit(consts.ROT_THREE)
                ctx.emit(consts.ROT_THREE)
            target.compile_store(ctx)
            ctx.emit(consts.DISCARD_TOP)


class MultiAssignment(Node):
    def __init__(self, assignable, value):
        self.assignable = assignable
        self.value = value

    def compile(self, ctx):
        self.value.compile(ctx)
        self.assignable.compile_store(ctx)

    def compile_defined(self, ctx):
        ConstantString("assignment").compile(ctx)


class Or(Node):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def compile(self, ctx):
        end = ctx.new_block()
        otherwise = ctx.new_block()

        self.lhs.compile(ctx)
        ctx.emit(consts.DUP_TOP)
        ctx.emit_jump(consts.JUMP_IF_TRUE, end)
        ctx.use_next_block(otherwise)
        ctx.emit(consts.DISCARD_TOP)
        self.rhs.compile(ctx)
        ctx.use_next_block(end)

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class And(Node):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def compile(self, ctx):
        end = ctx.new_block()
        otherwise = ctx.new_block()

        self.lhs.compile(ctx)
        ctx.emit(consts.DUP_TOP)
        ctx.emit_jump(consts.JUMP_IF_FALSE, end)
        ctx.use_next_block(otherwise)
        ctx.emit(consts.DISCARD_TOP)
        self.rhs.compile(ctx)
        ctx.use_next_block(end)

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class BaseSend(Node):
    def __init__(self, receiver, args, block_arg, lineno):
        Node.__init__(self, lineno)
        self.receiver = receiver
        self.args = args
        self.block_arg = block_arg

    def compile(self, ctx):
        with ctx.set_lineno(self.lineno):
            self.receiver.compile(ctx)
            if self.is_splat():
                for arg in self.args:
                    arg.compile(ctx)
                    if not isinstance(arg, Splat):
                        ctx.emit(consts.BUILD_ARRAY, 1)
            else:
                for arg in self.args:
                    arg.compile(ctx)
            block = self.get_block()
            if block is not None:
                block.compile(ctx)

            symbol = self.method_name_const(ctx)
            if self.is_splat() and block is not None:
                ctx.emit(self.send_block_splat, symbol, len(self.args) + 1)
            elif self.is_splat():
                ctx.emit(self.send_splat, symbol, len(self.args))
            elif block is not None:
                ctx.emit(self.send_block, symbol, len(self.args) + 1)
            else:
                ctx.emit(self.send, symbol, len(self.args))

    def is_splat(self):
        for arg in self.args:
            if isinstance(arg, Splat):
                return True
        return False

    def get_block(self):
        return self.block_arg

    def compile_receiver(self, ctx):
        self.receiver.compile(ctx)
        return 1

    def compile_load(self, ctx):
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.method), 0)

    def compile_store(self, ctx):
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.method + "="), 1)

    def compile_defined(self, ctx):
        self.compile_receiver(ctx)
        ctx.emit(self.defined, self.method_name_const(ctx))


class Send(BaseSend):
    send = consts.SEND
    send_block = consts.SEND_BLOCK
    send_splat = consts.SEND_SPLAT
    send_block_splat = consts.SEND_BLOCK_SPLAT
    defined = consts.DEFINED_METHOD

    def __init__(self, receiver, method, args, block_arg, lineno):
        BaseSend.__init__(self, receiver, args, block_arg, lineno)
        self.method = method

    def method_name_const(self, ctx):
        return ctx.create_symbol_const(self.method)


class Super(BaseSend):
    send_block = consts.SEND_SUPER_BLOCK
    send_block_splat = consts.SEND_SUPER_BLOCK_SPLAT
    defined = consts.DEFINED_SUPER

    def __init__(self, args, block_arg, lineno):
        BaseSend.__init__(self, Self(lineno), args, block_arg, lineno)

    def get_block(self):
        return BaseSend.get_block(self) or LoadBlock()

    def method_name_const(self, ctx):
        if ctx.code_name == "<main>":
            return ctx.create_const(ctx.space.w_nil)
        else:
            return ctx.create_symbol_const(ctx.code_name)


class Splat(Node):
    def __init__(self, value):
        self.value = value

    def compile_receiver(self, ctx):
        if self.value is None:
            return 0
        else:
            return self.value.compile_receiver(ctx)

    def compile_store(self, ctx):
        if self.value is not None:
            return self.value.compile_store(ctx)

    def compile(self, ctx):
        self.value.compile(ctx)
        ctx.emit(consts.COERCE_ARRAY, 1)


class HashSplat(Send):
    def __init__(self, receiver, lineno):
        Send.__init__(self, receiver, "to_hash", [], None, lineno)


class SendBlock(AbstractCallable):
    def __init__(self, lineno, block_args, splat_arg, post_args, kwargs, kwrest_arg, block_arg, block):
        Node.__init__(self, lineno)
        self.block_args = block_args
        self.splat_arg = splat_arg
        self.post_args = post_args
        self.kwargs = kwargs
        self.kwrest_arg = kwrest_arg
        self.block_arg = block_arg
        self.block = block

    def get_code_name(self, ctx):
        return "block in %s" % ctx.code_name

    def post_process_ctx(self, ctx, code_ctx):
        for cellname, kind in code_ctx.symtable.cells.iteritems():
            if kind == code_ctx.symtable.CELLVAR:
                code_ctx.symtable.get_cell_num(cellname)
        for name in ctx.symtable.cells:
            if (name not in code_ctx.symtable.cell_numbers and
                name not in code_ctx.symtable.cells):
                code_ctx.symtable.cells[name] = code_ctx.symtable.FREEVAR

    def compile(self, ctx):
        block_ctx = ctx.get_subctx(self.get_code_name(ctx), self)
        bc = self.compile_bytecode(
            ctx, block_ctx,
            self.block_args, self.splat_arg, self.post_args,
            self.kwargs, self.kwrest_arg, self.block_arg, self.block
        )
        ctx.emit(consts.LOAD_CONST, ctx.create_const(bc))

        cells = [None] * len(block_ctx.symtable.cell_numbers)
        for name, pos in block_ctx.symtable.cell_numbers.iteritems():
            cells[pos] = name
        num_cells = 0
        for name in reversed(cells):
            if block_ctx.symtable.cells[name] == block_ctx.symtable.FREEVAR:
                ctx.emit(consts.LOAD_CLOSURE, ctx.symtable.get_cell_num(name))
                num_cells += 1

        ctx.emit(consts.BUILD_BLOCK, num_cells)


class BlockArgument(Node):
    def __init__(self, value):
        self.value = value

    def compile(self, ctx):
        self.value.compile(ctx)
        ctx.emit(consts.COERCE_BLOCK)


class LoadBlock(BaseNode):
    def compile(self, ctx):
        ctx.emit(consts.LOAD_BLOCK)


class Subscript(Node):
    def __init__(self, target, args, lineno):
        Node.__init__(self, lineno)
        self.target = target
        self.args = args

    def compile(self, ctx):
        Send(self.target, "[]", self.args, None, self.lineno).compile(ctx)

    def compile_receiver(self, ctx):
        self.target.compile(ctx)
        if self.is_splat():
            for arg in self.args:
                arg.compile(ctx)
                if not isinstance(arg, Splat):
                    ctx.emit(consts.BUILD_ARRAY, 1)
            if len(self.args) != 1:
                ctx.emit(consts.BUILD_ARRAY_SPLAT, len(self.args))
        else:
            for arg in self.args:
                arg.compile(ctx)
            ctx.emit(consts.BUILD_ARRAY, len(self.args))
        return 2

    def compile_load(self, ctx):
        ctx.emit(consts.SEND_SPLAT, ctx.create_symbol_const("[]"), 1)

    def compile_store(self, ctx):
        ctx.emit(consts.BUILD_ARRAY, 1)
        ctx.emit(consts.SEND_SPLAT, ctx.create_symbol_const("[]="), 2)

    def is_splat(self):
        for arg in self.args:
            if isinstance(arg, Splat):
                return True
        return False


class Constant(Node):
    def __init__(self, name, lineno):
        Node.__init__(self, lineno)
        self.name = name

    def compile(self, ctx):
        with ctx.set_lineno(self.lineno):
            self.compile_receiver(ctx)
            self.compile_load(ctx)

    def compile_load(self, ctx):
        ctx.emit(consts.LOAD_LOCAL_CONSTANT, ctx.create_symbol_const(self.name))

    def compile_receiver(self, ctx):
        Scope(self.lineno).compile(ctx)
        return 1

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_CONSTANT, ctx.create_symbol_const(self.name))

    def compile_defined(self, ctx):
        self.compile_receiver(ctx)
        ctx.emit(consts.DEFINED_LOCAL_CONSTANT, ctx.create_symbol_const(self.name))


class LookupConstant(Node):
    def __init__(self, scope, name, lineno):
        Node.__init__(self, lineno)
        self.scope = scope
        self.name = name

    def compile(self, ctx):
        with ctx.set_lineno(self.lineno):
            self.compile_receiver(ctx)
            self.compile_load(ctx)

    def compile_receiver(self, ctx):
        if self.scope is not None:
            self.scope.compile(ctx)
        else:
            ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_object))
        return 1

    def compile_load(self, ctx):
        ctx.emit(consts.LOAD_CONSTANT, ctx.create_symbol_const(self.name))

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_CONSTANT, ctx.create_symbol_const(self.name))

    def compile_defined(self, ctx):
        self.compile_receiver(ctx)
        ctx.emit(consts.DEFINED_CONSTANT, ctx.create_symbol_const(self.name))


class Self(Node):
    def compile(self, ctx):
        ctx.emit(consts.LOAD_SELF)

    def compile_defined(self, ctx):
        ConstantString("self").compile(ctx)

    def compile_receiver(self, ctx):
        raise CompilerError("can't assign to self")


class Scope(Node):
    def compile(self, ctx):
        ctx.emit(consts.LOAD_SCOPE)


class Variable(Node):
    def __init__(self, name, lineno):
        Node.__init__(self, lineno)
        self.name = name

    def compile(self, ctx):
        ctx.emit(consts.LOAD_DEREF, ctx.symtable.get_cell_num(self.name))

    def compile_receiver(self, ctx):
        return 0

    def compile_load(self, ctx):
        self.compile(ctx)

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_DEREF, ctx.symtable.get_cell_num(self.name))

    def compile_defined(self, ctx):
        ConstantString("local-variable").compile(ctx)


class Global(Node):
    def __init__(self, name):
        self.name = name

    def compile(self, ctx):
        ctx.emit(consts.LOAD_GLOBAL, ctx.create_symbol_const(self.name))

    def compile_receiver(self, ctx):
        return 0

    def compile_load(self, ctx):
        self.compile(ctx)

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_GLOBAL, ctx.create_symbol_const(self.name))

    def compile_defined(self, ctx):
        ctx.emit(consts.DEFINED_GLOBAL, ctx.create_symbol_const(self.name))


class InstanceVariable(Node):
    def __init__(self, name):
        self.name = name

    def compile(self, ctx):
        self.compile_receiver(ctx)
        self.compile_load(ctx)

    def compile_receiver(self, ctx):
        ctx.emit(consts.LOAD_SELF)
        return 1

    def compile_load(self, ctx):
        ctx.emit(consts.LOAD_INSTANCE_VAR, ctx.create_symbol_const(self.name))

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_INSTANCE_VAR, ctx.create_symbol_const(self.name))

    def compile_defined(self, ctx):
        self.compile_receiver(ctx)
        ctx.emit(consts.DEFINED_INSTANCE_VAR, ctx.create_symbol_const(self.name))


class ClassVariable(Node):
    def __init__(self, name, lineno):
        Node.__init__(self, lineno)
        self.name = name

    def compile(self, ctx):
        with ctx.set_lineno(self.lineno):
            self.compile_receiver(ctx)
            self.compile_load(ctx)

    def compile_receiver(self, ctx):
        ctx.emit(consts.LOAD_SCOPE)
        return 1

    def compile_load(self, ctx):
        ctx.emit(consts.LOAD_CLASS_VAR, ctx.create_symbol_const(self.name))

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_CLASS_VAR, ctx.create_symbol_const(self.name))

    def compile_defined(self, ctx):
        self.compile_receiver(ctx)
        ctx.emit(consts.DEFINED_CLASS_VAR, ctx.create_symbol_const(self.name))


class Array(Node):
    def __init__(self, items):
        self.items = items

    def compile(self, ctx):
        n_items = 0
        n_components = 0
        for item in self.items:
            if isinstance(item, Splat):
                ctx.emit(consts.BUILD_ARRAY, n_items)
                item.compile(ctx)
                n_items = 0
                n_components += 2
            else:
                item.compile(ctx)
                n_items += 1
        if n_items or not n_components:
            ctx.emit(consts.BUILD_ARRAY, n_items)
            n_components += 1
        if n_components != 1:
            ctx.emit(consts.BUILD_ARRAY_SPLAT, n_components)

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class Hash(Node):
    def __init__(self, items):
        self.items = items

    def compile(self, ctx):
        ctx.emit(consts.BUILD_HASH)
        for k, v in self.items:
            ctx.emit(consts.DUP_TOP)
            k.compile(ctx)
            v.compile(ctx)
            ctx.emit(consts.SEND, ctx.create_symbol_const("[]="), 2)
            ctx.emit(consts.DISCARD_TOP)

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class Range(Node):
    def __init__(self, start, stop, exclusive):
        self.start = start
        self.stop = stop
        self.exclusive = exclusive

    def compile(self, ctx):
        self.start.compile(ctx)
        self.stop.compile(ctx)
        if self.exclusive:
            ctx.emit(consts.BUILD_RANGE_EXCLUSIVE)
        else:
            ctx.emit(consts.BUILD_RANGE)

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class ConstantNode(Node):
    def compile(self, ctx):
        ctx.emit(consts.LOAD_CONST, self.create_const(ctx))

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class ConstantInt(ConstantNode):
    def __init__(self, intvalue):
        self.intvalue = intvalue

    def negate(self):
        return ConstantInt(-self.intvalue)

    def create_const(self, ctx):
        return ctx.create_int_const(self.intvalue)


class ConstantBigInt(ConstantNode):
    def __init__(self, bigint):
        self.bigint = bigint

    def negate(self):
        return ConstantBigInt(self.bigint.neg())

    def create_const(self, ctx):
        return ctx.create_const(ctx.space.newbigint_fromrbigint(self.bigint))


class ConstantFloat(ConstantNode):
    def __init__(self, floatvalue):
        self.floatvalue = floatvalue

    def negate(self):
        return ConstantFloat(-self.floatvalue)

    def create_const(self, ctx):
        return ctx.create_float_const(self.floatvalue)


class ConstantSymbol(ConstantNode):
    def __init__(self, symbol):
        self.symbol = symbol

    def create_const(self, ctx):
        return ctx.create_symbol_const(self.symbol)


class ConstantString(ConstantNode):
    def __init__(self, strvalue):
        self.strvalue = strvalue

    def create_const(self, ctx):
        return ctx.create_symbol_const(self.strvalue)

    def compile(self, ctx):
        ConstantNode.compile(self, ctx)
        ctx.emit(consts.COERCE_STRING)


class ConstantRegexp(ConstantNode):
    def __init__(self, regexp, flags, lineno):
        ConstantNode.__init__(self, lineno)
        self.regexp = regexp
        self.flags = flags

    def create_const(self, ctx):
        try:
            w_regexp = ctx.space.newregexp(self.regexp, self.flags)
        except RegexpError as e:
            raise ctx.space.error(ctx.space.w_SyntaxError, "line %d: %s" % (self.lineno, e))
        return ctx.create_const(w_regexp)


class ConstantBool(ConstantNode):
    def __init__(self, boolval):
        self.boolval = boolval

    def create_const(self, ctx):
        return ctx.create_const(ctx.space.newbool(self.boolval))

    def compile_defined(self, ctx):
        ConstantString("true" if self.boolval else "false").compile(ctx)

    def compile_receiver(self, ctx):
        raise CompilerError("can't assign to %s" % ("true" if self.boolval else "false"))


class DynamicString(Node):
    def __init__(self, strvalues):
        self.strvalues = strvalues

    def compile(self, ctx):
        for strvalue in self.strvalues:
            strvalue.compile(ctx)
            if not isinstance(strvalue, ConstantString):
                ctx.emit(consts.SEND, ctx.create_symbol_const("to_s"), 0)
        if len(self.strvalues) != 1:
            ctx.emit(consts.BUILD_STRING, len(self.strvalues))

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class DynamicRegexp(Node):
    def __init__(self, dstring, flags):
        self.dstring = dstring
        self.flags = flags

    def compile(self, ctx):
        self.dstring.compile(ctx)
        ctx.emit(consts.LOAD_CONST, ctx.create_int_const(self.flags))
        ctx.emit(consts.BUILD_REGEXP)

    def compile_defined(self, ctx):
        ConstantString("expression").compile(ctx)


class Symbol(Node):
    def __init__(self, value, lineno):
        Node.__init__(self, lineno)
        self.value = value

    def compile(self, ctx):
        Send(self.value, "to_sym", [], None, self.lineno).compile(ctx)


class Nil(BaseNode):
    def compile(self, ctx):
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))

    def compile_defined(self, ctx):
        ConstantString("nil").compile(ctx)

    def compile_receiver(self, ctx):
        raise CompilerError("can't assign to nil")


class File(BaseNode):
    def compile(self, ctx):
        ctx.emit(consts.LOAD_CODE)
        ctx.emit(consts.SEND, ctx.create_symbol_const("filepath"), 0)

    def compile_receiver(self, ctx):
        raise CompilerError("can't assign to __FILE__")


class Line(Node):
    def compile(self, ctx):
        ConstantInt(self.lineno).compile(ctx)

    def compile_receiver(self, ctx):
        raise CompilerError("can't assign to __LINE__")
