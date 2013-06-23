from rpython.rlib.objectmodel import specialize
from rpython.rlib.rbigint import rbigint

from rply import ParserGenerator, Token, ParsingError
from rply.token import BaseBox, SourcePosition

from topaz import ast
from topaz.astcompiler import SymbolTable, BlockSymbolTable, SharedScopeSymbolTable
from topaz.utils import regexp


class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self._hidden_scopes = []

    def parse(self):
        l = LexerWrapper(self.lexer.tokenize())
        return self.parser.parse(l, state=self)

    def error(self, msg):
        # TODO: this should use a real SourcePosition
        return ParsingError(msg, SourcePosition(-1, -1, -1))

    def push_local_scope(self):
        self.lexer.symtable = SymbolTable(self.lexer.symtable)

    def push_block_scope(self):
        self.lexer.symtable = BlockSymbolTable(self.lexer.symtable)

    def push_shared_scope(self):
        self.lexer.symtable = SharedScopeSymbolTable(self.lexer.symtable)

    def save_and_pop_scope(self, node):
        child_symtable = self.lexer.symtable
        child_symtable.parent_symtable.add_subscope(node, child_symtable)
        self.lexer.symtable = child_symtable.parent_symtable

    def hide_scope(self):
        self._hidden_scopes.append(self.lexer.symtable)
        self.lexer.symtable = self.lexer.symtable.parent_symtable

    def unhide_scope(self):
        self.lexer.symtable = self._hidden_scopes.pop()

    def new_token(self, orig, name, value):
        return Token(name, value, orig.getsourcepos())

    def new_list(self, box=None):
        if box is None:
            contents = []
        else:
            contents = [box.getast()]
        return self._new_list(contents)

    def _new_list(self, nodes):
        return BoxASTList(nodes)

    def append_to_list(self, box_list, box):
        base = box_list.getastlist() if box_list is not None else []
        return BoxASTList(base + [box.getast()])

    def new_stmt(self, box):
        return self._new_stmt(box.getast())

    def _new_stmt(self, node):
        if not isinstance(node, ast.BaseStatement):
            node = ast.Statement(node)
        return BoxAST(node)

    def new_assignable_list(self, boxes):
        return self._new_assignable_list([box.getast() for box in boxes])

    def _new_assignable_list(self, nodes):
        return BoxAssignableList(nodes)

    def append_to_assignable_list(self, box_list, box):
        return self._append_to_assignable_list(box_list.getvars(), [box.getast()])

    def _append_to_assignable_list(self, vars, nodes):
        return BoxAssignableList(vars + nodes)

    def new_augmented_assignment(self, op, lhs, rhs):
        op = op.getstr()[:-1]
        target = lhs.getast()
        value = rhs.getast()
        if op == "||":
            node = ast.OrEqual(target, value)
        elif op == "&&":
            node = ast.AndEqual(target, value)
        else:
            node = ast.AugmentedAssignment(op, target, value)
        return BoxAST(node)

    def assignable(self, box):
        node = box.getast()
        if isinstance(node, ast.File):
            raise self.error("Can't assign to __FILE__")
        elif isinstance(node, ast.Line):
            raise self.error("Can't assign to __LINE__")
        elif isinstance(node, ast.Variable):
            self.lexer.symtable.declare_write(node.name)
        return box

    def _arg_to_variable(self, node):
        if isinstance(node, ast.Argument):
            self.lexer.symtable.declare_local(node.name)
            return ast.Variable(node.name, -1)
        elif isinstance(node, ast.MultiAssignable):
            return node
        else:
            raise SystemError

    def arg_to_variable(self, box):
        return self._arg_to_variable(box.getast())

    def args_to_variables(self, listbox):
        astlist = listbox.getastlist()
        variables = [None] * len(astlist)
        for i, node in enumerate(astlist):
            variables[i] = self._arg_to_variable(node)
        return variables

    def new_binary_call(self, lhs, op, rhs):
        return self._new_call(lhs.getast(), op, [rhs.getast()], None)

    def new_call(self, receiver, method, box_args):
        args = box_args.getcallargs() if box_args is not None else []
        block = box_args.getcallblock() if box_args is not None else None
        return self._new_call(receiver.getast(), method, args, block)

    def new_fcall(self, method, args):
        receiver = ast.Self(method.getsourcepos().lineno)
        return self._new_call(
            receiver, method,
            args.getcallargs() if args is not None else [],
            args.getcallblock() if args is not None else None,
        )

    def _new_call(self, receiver, method, args, block):
        return BoxAST(ast.Send(receiver, method.getstr(), args, block, method.getsourcepos().lineno))

    def new_and(self, lhs, rhs):
        return BoxAST(ast.And(lhs.getast(), rhs.getast()))

    def new_or(self, lhs, rhs):
        return BoxAST(ast.Or(lhs.getast(), rhs.getast()))

    def new_args(self, args=None, splat_arg=None, block_arg=None):
        return BoxArgs(
            args.getastlist() if args is not None else [],
            splat_arg.getstr() if splat_arg is not None else None,
            block_arg.getstr() if block_arg is not None else None,
        )

    def new_call_args(self, box_arg=None, box_block=None):
        args = [box_arg.getast()] if box_arg else []
        block = box_block.getast() if box_block is not None else None
        return self._new_call_args(args, block)

    def _new_call_args(self, args, block):
        return BoxCallArgs(args, block)

    def call_arg_block_pass(self, box_args, box_block_pass):
        if box_block_pass is None:
            return box_args
        return self._new_call_args(box_args.getcallargs(), box_block_pass.getast())

    def append_call_arg(self, box_arg, box):
        return self._new_call_args(box_arg.getcallargs() + [box.getast()], box_arg.getcallblock())

    def new_send_block(self, lineno, params, body):
        stmts = body.getastlist() if body is not None else []
        args = params.getargs(include_multi=True) if params is not None else []
        splat = params.getsplatarg() if params is not None else None
        block_arg = params.getblockarg() if params is not None else None

        extra_stmts = []
        for idx, arg in enumerate(args):
            if isinstance(arg, ast.MultiAssignable):
                new_arg = ast.Argument(str(idx))
                asgn = ast.MultiAssignment(arg, ast.Variable(new_arg.name, lineno))
                args[idx] = new_arg
                self.lexer.symtable.declare_argument(new_arg.name)
                extra_stmts.append(ast.Statement(asgn))

        extra_stmts.reverse()
        stmts = extra_stmts + stmts

        block = ast.Block(stmts) if stmts else ast.Nil()
        return BoxAST(ast.SendBlock(args, splat, block_arg, block))

    def combine_send_block(self, send_box, block_box):
        send = send_box.getast(ast.BaseSend)
        block = block_box.getast()
        if send.block_arg is not None:
            raise self.error("Both block arg and actual block given.")
        if isinstance(send, ast.Send):
            node = ast.Send(
                send.receiver,
                send.method,
                send.args,
                block,
                send.lineno
            )
        elif isinstance(send, ast.Super):
            node = ast.Super(
                send.args,
                block,
                send.lineno,
            )
        else:
            raise SystemError
        return BoxAST(node)

    def _array_or_node(self, box):
        args = box.getcallargs()
        if len(args) == 1:
            [node] = args
        else:
            node = ast.Array(args)
        return node

    def new_return(self, box):
        return BoxAST(ast.Return(self._array_or_node(box)))

    def new_next(self, box):
        return BoxAST(ast.Next(self._array_or_node(box)))

    def new_break(self, box):
        return BoxAST(ast.Break(self._array_or_node(box)))

    def new_super(self, args, token):
        return BoxAST(ast.Super(
            args.getcallargs() if args is not None else [],
            args.getcallblock() if args is not None else None,
            token.getsourcepos().lineno
        ))

    def new_splat(self, box):
        return BoxAST(ast.Splat(box.getast()))

    def new_colon2(self, box, constant):
        return BoxAST(ast.LookupConstant(box.getast(), constant.getstr(), constant.getsourcepos().lineno))

    def new_colon3(self, constant):
        return BoxAST(ast.LookupConstant(None, constant.getstr(), constant.getsourcepos().lineno))

    def new_defined(self, box, token):
        return BoxAST(ast.Defined(box.getast(), token.getsourcepos().lineno))

    def new_symbol(self, token):
        return BoxAST(ast.ConstantSymbol(token.getstr()))

    def new_hash(self, box):
        items = []
        raw_items = box.getastlist()
        for i in xrange(0, len(raw_items), 2):
            items.append((raw_items[i], raw_items[i + 1]))
        return BoxAST(ast.Hash(items))

    def new_global(self, box):
        return BoxAST(ast.Global(box.getstr()))

    def new_instance_var(self, box):
        return BoxAST(ast.InstanceVariable(box.getstr()))

    def new_class_var(self, box):
        return BoxAST(ast.ClassVariable(box.getstr(), box.getsourcepos().lineno))

    def concat_literals(self, head, tail):
        if head is None:
            return tail
        if tail is None:
            return head

        dynamic = False
        const_str = ""
        dyn_str_components = []
        for part in [head.getast(), tail.getast()]:
            if not dynamic:
                if isinstance(part, ast.ConstantString):
                    const_str += part.strvalue
                else:
                    dynamic = True
                    if const_str:
                        dyn_str_components.append(ast.ConstantString(const_str))
                    if isinstance(part, ast.DynamicString):
                        dyn_str_components.extend(part.strvalues)
                    else:
                        dyn_str_components.append(part)
            else:
                if isinstance(part, ast.DynamicString):
                    dyn_str_components.extend(part.strvalues)
                else:
                    dyn_str_components.append(part)
        if dynamic:
            node = ast.DynamicString(dyn_str_components)
        else:
            node = ast.ConstantString(const_str)
        return BoxAST(node)

    def _parse_int(self, box):
        s = box.getstr()
        if "X" in s:
            base = 16
        elif "O" in s:
            base = 8
        elif "B" in s:
            base = 2
        else:
            base = 10
        if base != 10:
            # Strip off the leading 0[xob]
            s = s[2:]

        val = rbigint()
        i = 0
        while i < len(s):
            c = ord(s[i])
            if ord("a") <= c <= ord("z"):
                digit = c - ord("a") + 10
            elif ord("A") <= c <= ord("Z"):
                digit = c - ord("A") + 10
            elif ord("0") <= c <= ord("9"):
                digit = c - ord("0")
            else:
                break
            if digit >= base:
                break
            val = val.mul(rbigint.fromint(base)).add(rbigint.fromint(digit))
            i += 1
        try:
            return ast.ConstantInt(val.toint())
        except OverflowError:
            return ast.ConstantBigInt(val)

    pg = ParserGenerator([
        "CLASS", "MODULE", "DEF", "UNDEF", "BEGIN", "RESCUE", "ENSURE", "END",
        "IF", "UNLESS", "THEN", "ELSIF", "ELSE", "CASE", "WHEN", "WHILE",
        "UNTIL", "FOR", "BREAK", "NEXT", "REDO", "RETRY", "IN", "DO",
        "DO_COND", "DO_BLOCK", "RETURN", "YIELD", "SUPER", "SELF", "NIL",
        "TRUE", "FALSE", "AND", "OR", "NOT", "IF_MOD", "UNLESS_MOD",
        "WHILE_MOD", "UNTIL_MOD", "RESCUE_MOD", "ALIAS", "DEFINED",
        "lBEGIN", "lEND", "__LINE__", "__FILE__", "__ENCODING__", "DO_LAMBDA",

        "IDENTIFIER", "FID", "GVAR", "IVAR", "CONSTANT", "CVAR", "LABEL",
        "CHAR", "UPLUS", "UMINUS", "UMINUS_NUM", "POW", "CMP", "EQ", "EQQ",
        "NEQ", "GEQ", "LEQ", "ANDOP", "OROP", "MATCH", "NMATCH", "DOT", "DOT2",
        "DOT3", "AREF", "ASET", "LSHFT", "RSHFT", "COLON2", "COLON3",
        "OP_ASGN", "ASSOC", "LPAREN", "LPAREN2", "RPAREN", "LPAREN_ARG",
        "LBRACK", "RBRACK", "LBRACE", "LBRACE_ARG", "STAR", "STAR2", "AMPER",
        "AMPER2", "TILDE", "PERCENT", "DIVIDE", "PLUS", "MINUS", "LT", "GT",
        "PIPE", "BANG", "CARET", "LCURLY", "RCURLY", "BACK_REF2", "SYMBEG",
        "STRING_BEG", "XSTRING_BEG", "REGEXP_BEG", "WORDS_BEG", "QWORDS_BEG",
        "STRING_DBEG", "STRING_DVAR", "STRING_END", "LAMBDA", "LAMBEG",
        "NTH_REF", "BACK_REF", "STRING_CONTENT", "INTEGER", "FLOAT",
        "REGEXP_END",

        "LITERAL_EQUAL", "LITERAL_COLON", "LITERAL_COMMA", "LITERAL_LBRACKET",
        "LITERAL_SEMICOLON", "LITERAL_QUESTION_MARK", "LITERAL_SPACE",
        "LITERAL_NEWLINE",
    ], precedence=[
        ("nonassoc", ["LOWEST"]),
        ("nonassoc", ["LBRACE_ARG"]),
        ("nonassoc", ["IF_MOD", "UNLESS_MOD", "WHILE_MOD", "UNTIL_MOD"]),
        ("left", ["OR", "AND"]),
        ("right", ["NOT"]),
        ("nonassoc", ["DEFINED"]),
        ("right", ["LITERAL_EQUAL", "OP_ASGN"]),
        ("left", ["RESCUE_MOD"]),
        ("right", ["LITERAL_QUESTION_MARK", "LITERAL_COLON"]),
        ("nonassoc", ["DOT2", "DOT3"]),
        ("left", ["OROP"]),
        ("left", ["ANDOP"]),
        ("nonassoc", ["CMP", "EQ", "EQQ", "NEQ", "MATCH", "NMATCH"]),
        ("left", ["GT", "GEQ", "LT", "LEQ"]),
        ("left", ["PIPE", "CARET"]),
        ("left", ["AMPER2"]),
        ("left", ["LSHFT", "RSHFT"]),
        ("left", ["PLUS", "MINUS"]),
        ("left", ["STAR2", "DIVIDE", "PERCENT"]),
        ("right", ["UMINUS_NUM", "UMINUS"]),
        ("right", ["POW"]),
        ("right", ["BANG", "TILDE", "UPLUS"]),
    ], cache_id="topaz")

    @pg.production("program : top_compstmt")
    def program(self, p):
        """
        program       : {
                  lexer.setState(LexState.EXPR_BEG);
                  support.initTopLocalVariables();
              } top_compstmt {
  // ENEBO: Removed !compile_for_eval which probably is to reduce warnings
                  if ($2 != null) {
                      /* last expression should not be void */
                      if ($2 instanceof BlockNode) {
                          support.checkUselessStatement($<BlockNode>2.getLast());
                      } else {
                          support.checkUselessStatement($2);
                      }
                  }
                  support.getResult().setAST(support.addRootNode($2, support.getPosition($2)));
              }
        """
        # TODO: sym table setup, and useless statement
        return BoxAST(ast.Main(ast.Block(p[0].getastlist()) if p[0] is not None else ast.Nil()))

    @pg.production("top_compstmt : top_stmts opt_terms")
    def top_compstmt(self, p):
        return p[0]

    @pg.production("top_stmts : none")
    def top_stmts_none(self, p):
        return p[0]

    @pg.production("top_stmts : top_stmt")
    def top_stmts_top_stmt(self, p):
        return self.new_list(p[0])

    @pg.production("top_stmts : top_stmts terms top_stmt")
    def top_stmts(self, p):
        return self.append_to_list(p[0], p[2])

    @pg.production("top_stmts : error top_stmt")
    def top_stmts_error(self, p):
        return p[1]

    @pg.production("top_stmt : stmt")
    def top_stmt_stmt(self, p):
        return p[0]

    @pg.production("top_stmt : lBEGIN LCURLY top_compstmt RCURLY")
    def top_stmt_lbegin(self, p):
        """
        top_stmt      : stmt
              | klBEGIN {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("BEGIN in method");
                    }
              } tLCURLY top_compstmt tRCURLY {
                    support.getResult().addBeginNode(new PreExe19Node($1.getPosition(), support.getCurrentScope(), $4));
                    $$ = null;
              }
        """
        raise NotImplementedError(p)

    @pg.production("bodystmt : compstmt opt_rescue opt_else opt_ensure")
    def bodystmt(self, p):
        body = ast.Block(p[0].getastlist()) if p[0] is not None else ast.Nil()
        if p[1] is not None:
            except_handlers = p[1].getastlist()
            body = ast.TryExcept(body, except_handlers, ast.Nil())
        elif p[2] is not None:
            body = ast.TryExcept(body, [], p[2].getast())
        if p[3] is not None:
            body = ast.TryFinally(body, ast.Block(p[3].getastlist()))
        return BoxAST(body)

    @pg.production("compstmt : stmts opt_terms")
    def compstmt(self, p):
        """
        compstmt        : stmts opt_terms {
                    if ($1 instanceof BlockNode) {
                        support.checkUselessStatements($<BlockNode>1);
                    }
                    $$ = $1;
                }
        """
        # TODO: checkUslessStatements?
        return p[0]

    @pg.production("stmts : none")
    def stmts_none(self, p):
        return p[0]

    @pg.production("stmts : stmt")
    def stmts_stmt(self, p):
        return self.new_list(p[0])

    @pg.production("stmts : stmts term stmt")
    def stmts(self, p):
        return self.append_to_list(p[0], p[2])

    @pg.production("stmts : error stmt")
    def stmts_error(self, p):
        return p[1]

    @pg.production("stmt : ALIAS fitem alias_after_fitem fitem")
    def stmt_alias_fitem(self, p):
        return BoxAST(ast.Alias(p[1].getast(), p[3].getast(), p[0].getsourcepos().lineno))

    @pg.production("alias_after_fitem : ")
    def alias_after_fitem(self, p):
        self.lexer.state = self.lexer.EXPR_FNAME

    @pg.production("stmt : ALIAS GVAR GVAR")
    def stmt_alias_gvar(self, p):
        """
        kALIAS tGVAR tGVAR {
                    $$ = new VAliasNode($1.getPosition(), (String) $2.getValue(), (String) $3.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : ALIAS GVAR BACK_REF")
    def stmt_alias_gvar_backref(self, p):
        """
        kALIAS tGVAR tBACK_REF {
                    $$ = new VAliasNode($1.getPosition(), (String) $2.getValue(), "$" + $<BackRefNode>3.getType());
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : ALIAS GVAR NTH_REF")
    def stmt_alias_gvar_nref(self, p):
        """
        kALIAS tGVAR tNTH_REF {
                    support.yyerror("can't make alias for the number variables");
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : UNDEF undef_list")
    def stmt_undef(self, p):
        return BoxAST(ast.Undef(p[1].getastlist(), p[0].getsourcepos().lineno))

    @pg.production("stmt : stmt IF_MOD expr_value")
    def stmt_ifmod(self, p):
        return self._new_stmt(ast.If(
            p[2].getast(),
            ast.Block([p[0].getast()]),
            ast.Nil(),
        ))

    @pg.production("stmt : stmt UNLESS_MOD expr_value")
    def stmt_unlessmod(self, p):
        return self._new_stmt(ast.If(
            p[2].getast(),
            ast.Nil(),
            ast.Block([p[0].getast()]),
        ))

    @pg.production("stmt : stmt WHILE_MOD expr_value")
    def stmt_while_mod(self, p):
        return self._new_stmt(ast.While(
            p[2].getast(),
            ast.Block([p[0].getast()])
        ))

    @pg.production("stmt : stmt UNTIL_MOD expr_value")
    def stmt_until_mod(self, p):
        return self._new_stmt(ast.Until(
            p[2].getast(),
            ast.Block([p[0].getast()])
        ))

    @pg.production("stmt : stmt RESCUE_MOD stmt")
    def stmt_rescue_mod(self, p):
        lineno = p[1].getsourcepos().lineno
        return self._new_stmt(ast.TryExcept(
            ast.Block([p[0].getast()]),
            [
                ast.ExceptHandler(
                    [ast.LookupConstant(ast.Scope(lineno), "StandardError", lineno)],
                    None,
                    ast.Block([p[2].getast()]),
                )
            ],
            ast.Nil()
        ))

    @pg.production("stmt : lEND LCURLY compstmt RCURLY")
    def stmt_lend(self, p):
        """
        klEND tLCURLY compstmt tRCURLY {
                    if (support.isInDef() || support.isInSingle()) {
                        support.warn(ID.END_IN_METHOD, $1.getPosition(), "END in method; use at_exit");
                    }
                    $$ = new PostExeNode($1.getPosition(), $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : command_asgn")
    def stmt_command_assign(self, p):
        return self.new_stmt(p[0])

    @pg.production("stmt : mlhs LITERAL_EQUAL command_call")
    def stmt_mlhs_equal_command_call(self, p):
        return self._new_stmt(ast.MultiAssignment(
            p[0].getassignment(),
            p[2].getast()
        ))

    @pg.production("stmt : var_lhs OP_ASGN command_call")
    def stmt_var_lhs_op_asgn_command_call(self, p):
        return self.new_stmt(self.new_augmented_assignment(p[1], p[0], p[2]))

    @pg.production("stmt : primary_value LITERAL_LBRACKET opt_call_args rbracket OP_ASGN command_call")
    def stmt_subscript_op_asgn_command_call(self, p):
        """
        primary_value '[' opt_call_args rbracket tOP_ASGN command_call {
  // FIXME: arg_concat logic missing for opt_call_args
                    $$ = support.new_opElementAsgnNode(support.getPosition($1), $1, (String) $5.getValue(), $3, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : primary_value DOT IDENTIFIER OP_ASGN command_call")
    def stmt_method_op_asgn_command_call(self, p):
        """
        primary_value tDOT tIDENTIFIER tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : primary_value DOT CONSTANT OP_ASGN command_call")
    def stmt_method_constant_op_asgn_command_call(self, p):
        """
        primary_value tDOT tCONSTANT tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : primary_value COLON2 CONSTANT OP_ASGN command_call")
    def stmt_primary_value_colon_constant_op_asgn_command_call(self, p):
        self.error("can't make alias for the number variables")

    @pg.production("stmt : primary_value COLON2 IDENTIFIER OP_ASGN command_call")
    def stmt_constant_op_asgn_command_call(self, p):
        """
        primary_value tCOLON2 tIDENTIFIER tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : backref OP_ASGN command_call")
    def stmt_backref_op_asgn_command_call(self, p):
        raise NotImplementedError(p)
        self.backref_assign_error(p[0])

    @pg.production("stmt : lhs LITERAL_EQUAL mrhs")
    def stmt_lhs_equal_mrhs(self, p):
        return self._new_stmt(ast.Assignment(p[0].getast(), ast.Array(p[2].getastlist())))

    @pg.production("stmt : mlhs LITERAL_EQUAL arg_value")
    def stmt_mlhs_equal_arg_value(self, p):
        return self._new_stmt(ast.MultiAssignment(
            p[0].getassignment(),
            p[2].getast()
        ))

    @pg.production("stmt : mlhs LITERAL_EQUAL mrhs")
    def stmt_mlhs_equal_mrhs(self, p):
        return self._new_stmt(ast.MultiAssignment(
            p[0].getassignment(),
            ast.Array(p[2].getastlist()),
        ))

    @pg.production("stmt : expr")
    def stmt_expr(self, p):
        return self.new_stmt(p[0])

    @pg.production("command_asgn : lhs LITERAL_EQUAL command_call")
    def command_asgn_lhs_equal_command_call(self, p):
        return BoxAST(ast.Assignment(
            p[0].getast(),
            p[2].getast()
        ))

    @pg.production("command_asgn : lhs LITERAL_EQUAL command_asgn")
    def command_asgn_lhs_equal_command_asgn(self, p):
        """
        lhs '=' command_asgn {
                    support.checkExpression($3);
                    $$ = support.node_assign($1, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("expr : command_call")
    def expr_command_call(self, p):
        return p[0]

    @pg.production("expr : expr AND expr")
    def expr_and(self, p):
        return self.new_and(p[0], p[2])

    @pg.production("expr : expr OR expr")
    def expr_or(self, p):
        return self.new_or(p[0], p[2])

    @pg.production("expr : NOT opt_nl expr")
    def expr_not(self, p):
        return self.new_call(p[2], self.new_token(p[0], "!", "!"), None)

    @pg.production("expr : BANG command_call")
    def expr_bang_command_call(self, p):
        raise NotImplementedError(p)

    @pg.production("expr : arg")
    def expr_arg(self, p):
        return p[0]

    @pg.production("expr_value : expr")
    def expr_value(self, p):
        """
        expr {
                    support.checkExpression($1);
                }
        """
        # TODO: checkExpression?
        return p[0]

    @pg.production("command_call : command")
    def command_call_command(self, p):
        return p[0]

    @pg.production("command_call : block_command")
    def command_call_block_command(self, p):
        return p[0]

    @pg.production("block_command : block_call")
    def block_command_block_call(self, p):
        return p[0]

    @pg.production("block_command : block_call DOT operation2 command_args")
    def block_command_dot(self, p):
        return self.new_call(p[0], p[2], p[3])

    @pg.production("block_command : block_call COLON2 operation2 command_args")
    def block_command_colon(self, p):
        """
        block_call tCOLON2 operation2 command_args {
                    $$ = support.new_call($1, $3, $4, null);
                }

        """
        raise NotImplementedError(p)

    @pg.production("cmd_brace_block : LBRACE_ARG push_block_scope opt_block_param compstmt RCURLY")
    def cmd_brace_block(self, p):
        box = self.new_send_block(p[0].getsourcepos().lineno, p[2], p[3])
        self.save_and_pop_scope(box.getast())
        return box

    @pg.production("command : operation command_args", precedence="LOWEST")
    def command_operation_command_args(self, p):
        return self.new_fcall(p[0], p[1])

    @pg.production("command : operation command_args cmd_brace_block")
    def command_operation_command_args_cmd_brace_block(self, p):
        return self.combine_send_block(self.new_fcall(p[0], p[1]), p[2])

    @pg.production("command : primary_value DOT operation2 command_args", precedence="LOWEST")
    def command_method_call_args(self, p):
        return self.new_call(p[0], p[2], p[3])

    @pg.production("command : primary_value DOT operation2 command_args cmd_brace_block")
    def command_method_call_args_brace_block(self, p):
        return self.combine_send_block(self.new_call(p[0], p[2], p[3]), p[4])

    @pg.production("command : primary_value COLON2 operation2 command_args", precedence="LOWEST")
    def command_colon_call_args(self, p):
        return self.new_call(p[0], p[2], p[3])

    @pg.production("command : primary_value COLON2 operation2 command_args cmd_brace_block")
    def command_colon_call_args_brace_block(self, p):
        """
        primary_value tCOLON2 operation2 command_args cmd_brace_block {
                    $$ = support.new_call($1, $3, $4, $5);
                }
        """
        raise NotImplementedError(p)

    @pg.production("command : SUPER command_args")
    def command_super(self, p):
        return self.new_super(p[1], p[0])

    @pg.production("command : YIELD command_args")
    def command_yield(self, p):
        return BoxAST(ast.Yield(p[1].getcallargs(), p[0].getsourcepos().lineno))

    @pg.production("command : RETURN call_args")
    def command_call_return(self, p):
        return self.new_return(p[1])

    @pg.production("command : BREAK call_args")
    def command_call_break(self, p):
        return self.new_break(p[1])

    @pg.production("command : NEXT call_args")
    def command_call_next(self, p):
        return self.new_next(p[1])

    @pg.production("mlhs : mlhs_basic")
    def mlhs(self, p):
        return p[0]

    @pg.production("mlhs : LPAREN mlhs_inner rparen")
    def mlhs_paren(self, p):
        return p[1]

    @pg.production("mlhs_inner : mlhs_basic")
    def mlhs_inner(self, p):
        return p[0]

    @pg.production("mlhs_inner : LPAREN mlhs_inner rparen")
    def mlhs_inner_paren(self, p):
        """
        tLPAREN mlhs_inner rparen {
                    $$ = new MultipleAsgn19Node($1.getPosition(), support.newArrayNode($1.getPosition(), $2), null, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : mlhs_head")
    def mlhs_basic_mlhs_head(self, p):
        return p[0]

    @pg.production("mlhs_basic : mlhs_head mlhs_item")
    def mlhs_basic_mlhs_head_mlhs_item(self, p):
        return self.append_to_assignable_list(p[0], p[1])

    @pg.production("mlhs_basic : mlhs_head STAR mlhs_node")
    def mlhs_basic_mlhs_head_star_node(self, p):
        return self.append_to_assignable_list(p[0], self.new_splat(p[2]))

    @pg.production("mlhs_basic : mlhs_head STAR mlhs_node LITERAL_COMMA mlhs_post")
    def mlhs_basic_mlhs_head_star_node_comma_post(self, p):
        box = self.append_to_assignable_list(p[0], self.new_splat(p[2]))
        return self._append_to_assignable_list(box.getvars(), p[4].getastlist())

    @pg.production("mlhs_basic : mlhs_head STAR")
    def mlhs_basic_mlhs_head_star(self, p):
        return self._append_to_assignable_list(p[0].getvars(), [ast.Splat(None)])

    @pg.production("mlhs_basic : mlhs_head STAR LITERAL_COMMA mlhs_post")
    def mlhs_basic_mlhs_head_star_comma_post(self, p):
        return self._append_to_assignable_list(p[0].getvars(), [ast.Splat(None)] + p[3].getastlist())

    @pg.production("mlhs_basic : STAR mlhs_node")
    def mlhs_basic_star_mlhs_node(self, p):
        return self.new_assignable_list([self.new_splat(p[1])])

    @pg.production("mlhs_basic : STAR mlhs_node LITERAL_COMMA mlhs_post")
    def mlhs_basic_star_mlhs_node_comma_post(self, p):
        return self._new_assignable_list([self.new_splat(p[1]).getast()] + p[3].getastlist())

    @pg.production("mlhs_basic : STAR")
    def mlhs_basic_star(self, p):
        return self._new_assignable_list([ast.Splat(None)])

    @pg.production("mlhs_basic : STAR LITERAL_COMMA mlhs_post")
    def mlhs_basic_star_comma_post(self, p):
        """
        tSTAR ',' mlhs_post {
                      $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_item : mlhs_node")
    def mlhs_item_node(self, p):
        return p[0]

    @pg.production("mlhs_item : LPAREN mlhs_inner rparen")
    def mlhs_item_paren(self, p):
        return BoxAST(p[1].getassignment())

    @pg.production("mlhs_head : mlhs_item LITERAL_COMMA")
    def mlhs_head_item(self, p):
        return self.new_assignable_list([p[0]])

    @pg.production("mlhs_head : mlhs_head mlhs_item LITERAL_COMMA")
    def mlhs_head_head_item(self, p):
        return self.append_to_assignable_list(p[0], p[1])

    @pg.production("mlhs_post : mlhs_item")
    def mlhs_post_item(self, p):
        return self.new_list(p[0])

    @pg.production("mlhs_post : mlhs_post LITERAL_COMMA mlhs_item")
    def mlhs_post_post_item(self, p):
        return self.append_to_list(p[0], p[2])

    @pg.production("mlhs_node : keyword_variable")
    @pg.production("mlhs_node : user_variable")
    def mlhs_node_variable(self, p):
        return self.assignable(p[0])

    @pg.production("mlhs_node : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def mlhs_node_subscript(self, p):
        return BoxAST(ast.Subscript(
            p[0].getast(),
            p[2].getcallargs(),
            p[1].getsourcepos().lineno
        ))

    @pg.production("mlhs_node : primary_value DOT IDENTIFIER")
    def mlhs_node_attr(self, p):
        return self.new_call(p[0], p[2], None)

    @pg.production("mlhs_node : primary_value COLON2 IDENTIFIER")
    def mlhs_node_colon_attr(self, p):
        """
        primary_value tCOLON2 tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_node : primary_value DOT CONSTANT")
    def mlhs_node_attr_constant(self, p):
        """
        primary_value tDOT tCONSTANT {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_node : primary_value COLON2 CONSTANT")
    def mlhs_node_constant(self, p):
        return BoxAST(ast.LookupConstant(p[0].getast(), p[2].getstr(), p[1].getsourcepos().lineno))

    @pg.production("mlhs_node : COLON3 CONSTANT")
    def mlhs_node_colon_constant(self, p):
        """
        tCOLON3 tCONSTANT {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("dynamic constant assignment");
                    }

                    ISourcePosition position = $1.getPosition();

                    $$ = new ConstDeclNode(position, null, support.new_colon3(position, (String) $2.getValue()), NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_node : backref")
    def mlhs_node_backref(self, p):
        """
        backref {
                    support.backrefAssignError($1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("lhs : keyword_variable")
    @pg.production("lhs : user_variable")
    def lhs_variable(self, p):
        return self.assignable(p[0])

    @pg.production("lhs : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def lhs_subscript(self, p):
        args = p[2].getcallargs() if p[2] is not None else []
        return BoxAST(ast.Subscript(p[0].getast(), args, p[1].getsourcepos().lineno))

    @pg.production("lhs : primary_value DOT IDENTIFIER")
    def lhs_dot_identifier(self, p):
        return self.new_call(p[0], p[2], None)

    @pg.production("lhs : primary_value COLON2 IDENTIFIER")
    def lhs_colon_identifier(self, p):
        return self.new_call(p[0], p[2], None)

    @pg.production("lhs : primary_value DOT CONSTANT")
    def lhs_dot_constant(self, p):
        """
        primary_value tDOT tCONSTANT {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("lhs : primary_value COLON2 CONSTANT")
    def lhs_colon_constant(self, p):
        return self.new_colon2(p[0], p[2])

    @pg.production("lhs : COLON3 CONSTANT")
    def lhs_unbound_colon_constant(self, p):
        return self.new_colon3(p[1])

    @pg.production("lhs : backref")
    def lhs_backref(self, p):
        raise NotImplementedError(p)
        self.backref_assign_error()

    @pg.production("cname : IDENTIFIER")
    def cname_identifier(self, p):
        raise self.error("class/module name must be CONSTANT")

    @pg.production("cname : CONSTANT")
    def cname_constant(self, p):
        return p[0]

    @pg.production("cpath : COLON3 cname")
    def cpath_unbound_colon_cname(self, p):
        return self.new_colon3(p[1])

    @pg.production("cpath : cname")
    def cpath_cname(self, p):
        lineno = p[0].getsourcepos().lineno
        return BoxAST(ast.LookupConstant(ast.Scope(lineno), p[0].getstr(), lineno))

    @pg.production("cpath : primary_value COLON2 cname")
    def cpath_colon_cname(self, p):
        return BoxAST(ast.LookupConstant(p[0].getast(), p[2].getstr(), p[1].getsourcepos().lineno))

    @pg.production("fname : IDENTIFIER")
    def fname_identifier(self, p):
        return p[0]

    @pg.production("fname : CONSTANT")
    def fname_constant(self, p):
        return p[0]

    @pg.production("fname : FID")
    def fname_fid(self, p):
        return p[0]

    @pg.production("fname : op")
    def fname_op(self, p):
        self.lexer.state = self.lexer.EXPR_ENDFN
        return p[0]

    @pg.production("fname : reswords")
    def fname_reswords(self, p):
        self.lexer.state = self.lexer.EXPR_ENDFN
        return p[0]

    @pg.production("fsym : fname")
    def fsym_fname(self, p):
        return self.new_symbol(p[0])

    @pg.production("fsym : symbol")
    def fsym_symbol(self, p):
        return self.new_symbol(p[0])

    @pg.production("fitem : fsym")
    def fitem_fsym(self, p):
        return p[0]

    @pg.production("fitem : dsym")
    def fitem_dsym(self, p):
        return p[0]

    @pg.production("undef_list : fitem")
    def undef_list_fitem(self, p):
        return self.new_list(p[0])

    @pg.production("undef_list : undef_list LITERAL_COMMA fitem")
    def undef_list_undef_list(self, p):
        """
        undef_list ',' {
                    lexer.setState(LexState.EXPR_FNAME);
                } fitem {
                    $$ = support.appendToBlock($1, support.newUndef($1.getPosition(), $4));
                }
        """
        raise NotImplementedError(p)

    @pg.production("op : PIPE")
    @pg.production("op : CARET")
    @pg.production("op : AMPER2")
    @pg.production("op : CMP")
    @pg.production("op : EQ")
    @pg.production("op : EQQ")
    @pg.production("op : MATCH")
    @pg.production("op : NMATCH")
    @pg.production("op : GT")
    @pg.production("op : GEQ")
    @pg.production("op : LT")
    @pg.production("op : LEQ")
    @pg.production("op : NEQ")
    @pg.production("op : LSHFT")
    @pg.production("op : RSHFT")
    @pg.production("op : PLUS")
    @pg.production("op : MINUS")
    @pg.production("op : STAR2")
    @pg.production("op : STAR")
    @pg.production("op : DIVIDE")
    @pg.production("op : PERCENT")
    @pg.production("op : POW")
    @pg.production("op : BANG")
    @pg.production("op : TILDE")
    @pg.production("op : UPLUS")
    @pg.production("op : UMINUS")
    @pg.production("op : AREF")
    @pg.production("op : ASET")
    @pg.production("op : BACK_REF2")
    def op(self, p):
        return p[0]

    @pg.production("reswords : __LINE__")
    @pg.production("reswords : __FILE__")
    @pg.production("reswords : __ENCODING__")
    @pg.production("reswords : lBEGIN")
    @pg.production("reswords : lEND")
    @pg.production("reswords : ALIAS")
    @pg.production("reswords : AND")
    @pg.production("reswords : BEGIN")
    @pg.production("reswords : BREAK")
    @pg.production("reswords : CASE")
    @pg.production("reswords : CLASS")
    @pg.production("reswords : DEF")
    @pg.production("reswords : DEFINED")
    @pg.production("reswords : DO")
    @pg.production("reswords : ELSE")
    @pg.production("reswords : ELSIF")
    @pg.production("reswords : END")
    @pg.production("reswords : ENSURE")
    @pg.production("reswords : FALSE")
    @pg.production("reswords : FOR")
    @pg.production("reswords : IN")
    @pg.production("reswords : MODULE")
    @pg.production("reswords : NEXT")
    @pg.production("reswords : NIL")
    @pg.production("reswords : NOT")
    @pg.production("reswords : OR")
    @pg.production("reswords : REDO")
    @pg.production("reswords : RESCUE")
    @pg.production("reswords : RETRY")
    @pg.production("reswords : RETURN")
    @pg.production("reswords : SELF")
    @pg.production("reswords : SUPER")
    @pg.production("reswords : THEN")
    @pg.production("reswords : TRUE")
    @pg.production("reswords : UNDEF")
    @pg.production("reswords : WHEN")
    @pg.production("reswords : YIELD")
    @pg.production("reswords : IF_MOD")
    @pg.production("reswords : UNLESS_MOD")
    @pg.production("reswords : WHILE_MOD")
    @pg.production("reswords : UNTIL_MOD")
    @pg.production("reswords : RESCUE_MOD")
    def reswords(self, p):
        return p[0]

    @pg.production("arg : lhs LITERAL_EQUAL arg")
    def arg_lhs_equal_arg(self, p):
        return BoxAST(ast.Assignment(p[0].getast(), p[2].getast()))

    @pg.production("arg : lhs LITERAL_EQUAL arg RESCUE_MOD arg")
    def arg_lhs_equal_arg_rescue_mod(self, p):
        lineno = p[1].getsourcepos().lineno
        return BoxAST(ast.Assignment(
            p[0].getast(),
            ast.TryExcept(
                p[2].getast(),
                [
                    ast.ExceptHandler(
                        [ast.LookupConstant(ast.Scope(lineno), "StandardError", lineno)],
                        None,
                        p[4].getast()
                    )
                ],
                ast.Nil()
            )
        ))

    @pg.production("arg : var_lhs OP_ASGN arg")
    def arg_var_lhs_op_asgn_arg(self, p):
        return self.new_augmented_assignment(p[1], p[0], p[2])

    @pg.production("arg : var_lhs OP_ASGN arg RESCUE_MOD arg")
    def arg_var_lhs_op_asgn_arg_rescue_mod(self, p):
        lineno = p[3].getsourcepos().lineno
        return self.new_augmented_assignment(
            p[1],
            p[0],
            BoxAST(ast.TryExcept(
                p[2].getast(),
                [
                    ast.ExceptHandler(
                        [ast.LookupConstant(ast.Scope(lineno), "StandardError", lineno)],
                        None,
                        p[4].getast()
                    )
                ],
                ast.Nil()
            ))
        )

    @pg.production("arg : primary_value LITERAL_LBRACKET opt_call_args rbracket OP_ASGN arg")
    def arg_subscript_op_asgn_arg(self, p):
        args = p[2].getcallargs() if p[2] is not None else []
        return self.new_augmented_assignment(
            p[4],
            BoxAST(ast.Subscript(p[0].getast(), args, p[1].getsourcepos().lineno)),
            p[5],
        )

    @pg.production("arg : primary_value DOT IDENTIFIER OP_ASGN arg")
    def arg_method_op_asgn_arg(self, p):
        return self.new_augmented_assignment(
            p[3],
            self.new_call(p[0], p[2], None),
            p[4]
        )

    @pg.production("arg : primary_value DOT CONSTANT OP_ASGN arg")
    def arg_method_constant_op_asgn_arg(self, p):
        """
        primary_value tDOT tCONSTANT tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : primary_value COLON2 IDENTIFIER OP_ASGN arg")
    def arg_colon_method_op_asgn_arg(self, p):
        """
        primary_value tCOLON2 tIDENTIFIER tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : primary_value COLON2 CONSTANT OP_ASGN arg")
    def arg_constant_op_asgn_arg(self, p):
        raise self.error("constant re-assignment")

    @pg.production("arg : COLON3 CONSTANT OP_ASGN arg")
    def arg_unbound_constant_op_asgn_arg(self, p):
        raise self.error("constant re-assignment")

    @pg.production("arg : backref OP_ASGN arg")
    def arg_backref_op_asgn_arg(self, p):
        raise NotImplementedError(p)
        self.backref_assign_error()

    @pg.production("arg : arg DOT2 arg")
    def arg_dot2(self, p):
        return BoxAST(ast.Range(p[0].getast(), p[2].getast(), False))

    @pg.production("arg : arg DOT3 arg")
    def arg_dot3(self, p):
        return BoxAST(ast.Range(p[0].getast(), p[2].getast(), True))

    @pg.production("arg : arg POW arg")
    @pg.production("arg : arg PERCENT arg")
    @pg.production("arg : arg DIVIDE arg")
    @pg.production("arg : arg STAR2 arg")
    @pg.production("arg : arg MINUS arg")
    @pg.production("arg : arg PLUS arg")
    def arg_binop(self, p):
        return self.new_binary_call(p[0], p[1], p[2])

    @pg.production("arg : UMINUS_NUM INTEGER POW arg")
    def arg_uminus_num_integer_pow_arg(self, p):
        lineno = p[0].getsourcepos().lineno
        return BoxAST(ast.Send(
            self.new_binary_call(BoxAST(self._parse_int(p[1])), p[2], p[3]).getast(),
            "-@",
            [],
            None,
            lineno
        ))

    @pg.production("arg : UMINUS_NUM FLOAT POW arg")
    def arg_uminus_num_float_pow_arg(self, p):
        lineno = p[0].getsourcepos().lineno
        return BoxAST(ast.Send(
            self.new_binary_call(BoxAST(ast.ConstantFloat(float(p[1].getstr()))), p[2], p[3]).getast(),
            "-@",
            [],
            None,
            lineno
        ))

    @pg.production("arg : UPLUS arg")
    def arg_uplus_arg(self, p):
        return BoxAST(ast.Send(p[1].getast(), "+@", [], None, p[0].getsourcepos().lineno))

    @pg.production("arg : UMINUS arg")
    def arg_uminus_arg(self, p):
        return BoxAST(ast.Send(p[1].getast(), "-@", [], None, p[0].getsourcepos().lineno))

    @pg.production("arg : arg NEQ arg")
    @pg.production("arg : arg EQQ arg")
    @pg.production("arg : arg EQ arg")
    @pg.production("arg : arg LEQ arg")
    @pg.production("arg : arg LT arg")
    @pg.production("arg : arg GEQ arg")
    @pg.production("arg : arg GT arg")
    @pg.production("arg : arg CMP arg")
    @pg.production("arg : arg AMPER2 arg")
    @pg.production("arg : arg CARET arg")
    @pg.production("arg : arg PIPE arg")
    def arg_binop2(self, p):
        return self.new_binary_call(p[0], p[1], p[2])

    @pg.production("arg : arg NMATCH arg")
    @pg.production("arg : arg MATCH arg")
    def arg_match_arg(self, p):
        return self.new_binary_call(p[0], p[1], p[2])

    @pg.production("arg : BANG arg")
    def arg_bang_arg(self, p):
        return self.new_call(p[1], p[0], None)

    @pg.production("arg : TILDE arg")
    def arg_tilde_arg(self, p):
        return self.new_call(p[1], p[0], None)

    @pg.production("arg : arg RSHFT arg")
    @pg.production("arg : arg LSHFT arg")
    def arg_binop3(self, p):
        return self.new_binary_call(p[0], p[1], p[2])

    @pg.production("arg : arg ANDOP arg")
    def arg_andop_arg(self, p):
        return self.new_and(p[0], p[2])

    @pg.production("arg : arg OROP arg")
    def arg_orop_arg(self, p):
        return self.new_or(p[0], p[2])

    @pg.production("arg : DEFINED opt_nl arg")
    def arg_defined(self, p):
        return self.new_defined(p[2], p[0])

    @pg.production("arg : arg LITERAL_QUESTION_MARK arg opt_nl LITERAL_COLON arg")
    def arg_ternary(self, p):
        return BoxAST(ast.If(
            p[0].getast(),
            p[2].getast(),
            p[5].getast()
        ))

    @pg.production("arg : primary")
    def arg_primary(self, p):
        return p[0]

    @pg.production("arg_value : arg")
    def arg_value(self, p):
        """
        arg {
                    support.checkExpression($1);
                    $$ = $1 != null ? $1 : NilImplicitNode.NIL;
                }
        """
        # TODO: check_expression, none handling
        return p[0]

    @pg.production("aref_args : none")
    def aref_args_none(self, p):
        return p[0]

    @pg.production("aref_args : args trailer")
    def aref_args_args_trailer(self, p):
        return p[0]

    @pg.production("aref_args : args LITERAL_COMMA assocs trailer")
    def aref_args_args_comma_assocs_trailer(self, p):
        return self.append_call_arg(p[0], self.new_hash(p[2]))

    @pg.production("aref_args : assocs trailer")
    def aref_args_assocs_trailer(self, p):
        return self.new_call_args(self.new_hash(p[0]))

    @pg.production("paren_args : LPAREN2 opt_call_args rparen")
    def paren_args(self, p):
        return p[1]

    @pg.production("opt_paren_args : none")
    def opt_paren_args_none(self, p):
        return p[0]

    @pg.production("opt_paren_args : paren_args")
    def opt_paren_args(self, p):
        return p[0]

    @pg.production("opt_call_args : none")
    def opt_call_args_none(self, p):
        return p[0]

    @pg.production("opt_call_args : call_args")
    def opt_call_args(self, p):
        return p[0]

    @pg.production("opt_call_args : args LITERAL_COMMA")
    def opt_call_args_args_comma(self, p):
        return p[0]

    @pg.production("opt_call_args : args LITERAL_COMMA assocs LITERAL_COMMA")
    def opt_call_args_args_comma_assocs_comma(self, p):
        return self.append_call_arg(p[0], self.new_hash(p[2]))

    @pg.production("opt_call_args : assocs LITERAL_COMMA")
    def opt_call_args_assocs_comma(self, p):
        return self.new_call_args(self.new_hash(p[0]))

    @pg.production("call_args : command")
    def call_args_command(self, p):
        return self.new_call_args(p[0])

    @pg.production("call_args : args opt_block_arg")
    def call_args_args_opt_block_arg(self, p):
        return self.call_arg_block_pass(p[0], p[1])

    @pg.production("call_args : assocs opt_block_arg")
    def call_args_assocs_opt_block_arg(self, p):
        box = self.new_call_args(self.new_hash(p[0]))
        return self.call_arg_block_pass(box, p[1])

    @pg.production("call_args : args LITERAL_COMMA assocs opt_block_arg")
    def call_args_args_comma_assocs_opt_block_arg(self, p):
        box = self.append_call_arg(p[0], self.new_hash(p[2]))
        return self.call_arg_block_pass(box, p[3])

    @pg.production("call_args : block_arg")
    def call_args_block_arg(self, p):
        return self.new_call_args(None, box_block=p[0])

    @pg.production("command_args : start_command_args call_args")
    def command_args(self, p):
        self.lexer.cmd_argument_state.reset(p[0].getint())
        return p[1]

    @pg.production("start_command_args : ")
    def start_command_args(self, p):
        return BoxInt(self.lexer.cmd_argument_state.begin())

    @pg.production("block_arg : AMPER arg_value")
    def block_arg(self, p):
        return BoxAST(ast.BlockArgument(p[1].getast()))

    @pg.production("opt_block_arg : LITERAL_COMMA block_arg")
    def opt_block_arg(self, p):
        return p[1]

    @pg.production("opt_block_arg : none_block_pass")
    def opt_block_arg_none(self, p):
        return p[0]

    @pg.production("args : arg_value")
    def args_arg_value(self, p):
        return self.new_call_args(p[0])

    @pg.production("args : STAR arg_value")
    def args_star_arg_value(self, p):
        return self.new_call_args(self.new_splat(p[1]))

    @pg.production("args : args LITERAL_COMMA arg_value")
    def args_comma_arg_value(self, p):
        return self.append_call_arg(p[0], p[2])

    @pg.production("args : args LITERAL_COMMA STAR arg_value")
    def args_comma_star_arg_value(self, p):
        return self.append_call_arg(p[0], self.new_splat(p[3]))

    @pg.production("mrhs : args LITERAL_COMMA arg_value")
    def mrhs_args_comma_arg_value(self, p):
        return self.append_to_list(self._new_list(p[0].getcallargs()), p[2])

    @pg.production("mrhs : args LITERAL_COMMA STAR arg_value")
    def mrhs_args_comma_star_arg_value(self, p):
        return self.append_to_list(self._new_list(p[0].getcallargs()), self.new_splat(p[3]))

    @pg.production("mrhs : STAR arg_value")
    def mrhs_star_arg_value(self, p):
        return self.new_list(self.new_splat(p[1]))

    @pg.production("primary : literal")
    def primary_literal(self, p):
        return p[0]

    @pg.production("primary : strings")
    def primary_strings(self, p):
        return p[0]

    @pg.production("primary : xstring")
    def primary_xstring(self, p):
        return p[0]

    @pg.production("primary : regexp")
    def primary_regexp(self, p):
        return p[0]

    @pg.production("primary : words")
    def primary_words(self, p):
        return p[0]

    @pg.production("primary : qwords")
    def primary_qwords(self, p):
        return p[0]

    @pg.production("primary : var_ref")
    def primary_var_ref(self, p):
        return p[0]

    @pg.production("primary : backref")
    def primary_backref(self, p):
        return p[0]

    @pg.production("primary : FID")
    def primary_fid(self, p):
        return self.new_fcall(p[0], None)

    @pg.production("primary : BEGIN bodystmt END")
    def primary_begin_end(self, p):
        return p[1]

    @pg.production("primary : LPAREN_ARG expr paren_post_expr rparen")
    def primary_paren_arg(self, p):
        return p[1]

    @pg.production("paren_post_expr : ")
    def paren_post_expr(self, p):
        self.lexer.state = self.lexer.EXPR_ENDARG

    @pg.production("primary : LPAREN compstmt RPAREN")
    def primary_lparen(self, p):
        node = ast.Block(p[1].getastlist()) if p[1] is not None else ast.Nil()
        return BoxAST(node)

    @pg.production("primary : primary_value COLON2 CONSTANT")
    def primary_constant_lookup(self, p):
        return self.new_colon2(p[0], p[2])

    @pg.production("primary : COLON3 CONSTANT")
    def primary_unbound_constant(self, p):
        return self.new_colon3(p[1])

    @pg.production("primary : LBRACK aref_args RBRACK")
    def primary_array(self, p):
        if p[1] is None:
            items = []
        else:
            items = p[1].getcallargs()
        return BoxAST(ast.Array(items))

    @pg.production("primary : LBRACE assoc_list RCURLY")
    def primary_hash(self, p):
        return self.new_hash(p[1])

    @pg.production("primary : RETURN")
    def primary_return(self, p):
        return BoxAST(ast.Return(ast.Nil()))

    @pg.production("primary : YIELD LPAREN2 call_args rparen")
    def primary_yield_paren_args(self, p):
        return BoxAST(ast.Yield(p[2].getcallargs(), p[0].getsourcepos().lineno))

    @pg.production("primary : YIELD LPAREN2 rparen")
    def primary_yield_paren(self, p):
        return BoxAST(ast.Yield([], p[0].getsourcepos().lineno))

    @pg.production("primary : YIELD")
    def primary_yield(self, p):
        return BoxAST(ast.Yield([], p[0].getsourcepos().lineno))

    @pg.production("primary : DEFINED opt_nl LPAREN2 expr rparen")
    def primary_defined(self, p):
        return self.new_defined(p[3], p[0])

    @pg.production("primary : NOT LPAREN2 expr rparen")
    def primary_not_paren_expr(self, p):
        return self.new_call(p[2], self.new_token(p[0], "!", "!"), None)

    @pg.production("primary : NOT LPAREN2 rparen")
    def primary_not_paren(self, p):
        return self.new_call(BoxAST(ast.Nil()), self.new_token(p[0], "!", "!"), None)

    @pg.production("primary : operation brace_block")
    def primary_operation_brace_block(self, p):
        return self.new_fcall(p[0], self.new_call_args(box_block=p[1]))

    @pg.production("primary : method_call")
    def primary_method_call(self, p):
        return p[0]

    @pg.production("primary : method_call brace_block")
    def primary_method_call_brace_block(self, p):
        return self.combine_send_block(p[0], p[1])

    @pg.production("primary : LAMBDA lambda")
    def primary_lambda(self, p):
        return p[1]

    @pg.production("primary : IF expr_value then compstmt if_tail END")
    def primary_if(self, p):
        return BoxAST(ast.If(
            p[1].getast(),
            ast.Block(p[3].getastlist()) if p[3] else ast.Nil(),
            p[4].getast() if p[4] else ast.Nil()
        ))

    @pg.production("primary : UNLESS expr_value then compstmt opt_else END")
    def primary_unless(self, p):
        return BoxAST(ast.If(
            p[1].getast(),
            p[4].getast() if p[4] is not None else ast.Nil(),
            ast.Block(p[3].getastlist()) if p[3] else ast.Nil(),
        ))

    @pg.production("primary : while expr_value do post_while_do compstmt END")
    def primary_while(self, p):
        body = ast.Block(p[4].getastlist()) if p[4] is not None else ast.Nil()
        return BoxAST(ast.While(p[1].getast(), body))

    @pg.production("while : WHILE")
    def while_token(self, p):
        self.lexer.condition_state.begin()

    @pg.production("post_while_do : ")
    def post_while_do(self, p):
        self.lexer.condition_state.end()

    @pg.production("primary : until expr_value do post_while_do compstmt END")
    def primary_until(self, p):
        body = ast.Block(p[4].getastlist()) if p[4] is not None else ast.Nil()
        return BoxAST(ast.Until(p[1].getast(), body))

    @pg.production("until : UNTIL")
    def until_token(self, p):
        self.lexer.condition_state.begin()

    @pg.production("primary : CASE expr_value opt_terms case_body END")
    def primary_case_expr_value(self, p):
        elsebody = p[3].getastlist()[-1]
        assert isinstance(elsebody, ast.When)
        assert elsebody.conds is None
        return BoxAST(ast.Case(
            p[1].getast(),
            p[3].getastlist()[:-1],
            elsebody.block,
        ))

    @pg.production("primary : CASE opt_terms case_body END")
    def primary_case(self, p):
        elsebody = p[2].getastlist()[-1]
        assert isinstance(elsebody, ast.When)
        assert elsebody.conds is None

        conditions = []
        for when in p[2].getastlist()[:-1]:
            assert isinstance(when, ast.When)
            cond = when.conds[0]
            for expr in when.conds[1:]:
                cond = ast.Or(cond, expr)
            conditions.append((cond, when.block))

        else_block = elsebody.block
        for idx in range(len(conditions) - 1, 0, -1):
            cond, block = conditions[idx]
            else_block = ast.If(cond, block, else_block)

        return BoxAST(ast.If(conditions[0][0], conditions[0][1], else_block))

    @pg.production("primary : for for_var IN post_for_in expr_value do post_for_do compstmt END")
    def primary_for(self, p):
        lineno = p[0].getsourcepos().lineno
        for_vars = p[1].get_for_var()
        arg = p[1].getargument()

        target = ast.Variable(arg.name, lineno)
        if isinstance(for_vars, BoxAST):
            asgn = ast.Assignment(for_vars.getast(), target)
        elif isinstance(for_vars, BoxAssignableList):
            asgn = ast.MultiAssignment(for_vars.getassignment(), target)
        else:
            raise SystemError

        stmts = p[7].getastlist() if p[7] is not None else []
        stmts = [ast.Statement(asgn)] + stmts
        block = ast.SendBlock([arg], None, None, ast.Block(stmts))

        self.save_and_pop_scope(block)
        return BoxAST(ast.Send(p[4].getast(), "each", [], block, lineno))

    @pg.production("for : FOR")
    def for_prod(self, p):
        self.push_shared_scope()
        return p[0]

    @pg.production("post_for_in : ")
    def post_for_in(self, p):
        self.lexer.condition_state.begin()
        self.hide_scope()

    @pg.production("post_for_do : ")
    def post_for_do(self, p):
        self.lexer.condition_state.end()
        self.unhide_scope()

    @pg.production("primary : CLASS cpath superclass push_local_scope bodystmt END")
    def primary_class(self, p):
        node = p[1].getast(ast.LookupConstant)
        node = ast.Class(
            node.scope,
            node.name,
            p[2].getast() if p[2] is not None else None,
            p[4].getast(),
        )
        self.save_and_pop_scope(node)
        return BoxAST(node)

    @pg.production("push_local_scope : ")
    def push_local_scope_prod(self, p):
        self.push_local_scope()

    @pg.production("primary : CLASS LSHFT expr term push_local_scope bodystmt END")
    def primary_singleton_class(self, p):
        node = ast.SingletonClass(
            p[2].getast(),
            p[5].getast(),
            p[0].getsourcepos().lineno
        )
        self.save_and_pop_scope(node)
        return BoxAST(node)

    @pg.production("primary : MODULE cpath push_local_scope bodystmt END")
    def primary_module(self, p):
        node = p[1].getast(ast.LookupConstant)
        node = ast.Module(node.scope, node.name, p[3].getast())
        self.save_and_pop_scope(node)
        return BoxAST(node)

    @pg.production("primary : DEF fname push_local_scope f_arglist bodystmt END")
    def primary_def(self, p):
        body = p[3].getfullbody(p[4].getast())
        node = ast.Function(
            None,
            p[1].getstr(),
            p[3].getargs(),
            p[3].getsplatarg(),
            p[3].getblockarg(),
            body
        )
        self.save_and_pop_scope(node)
        return BoxAST(node)

    @pg.production("primary : DEF singleton dot_or_colon singleton_method_post_dot_colon fname push_local_scope singleton_method_post_fname f_arglist bodystmt END")
    def primary_def_singleton(self, p):
        body = p[7].getfullbody(p[8].getast())
        node = ast.Function(
            p[1].getast(),
            p[4].getstr(),
            p[7].getargs(),
            p[7].getsplatarg(),
            p[7].getblockarg(),
            body,
        )
        self.save_and_pop_scope(node)
        return BoxAST(node)

    @pg.production("singleton_method_post_dot_colon : ")
    def singleton_method_post_dot_colon(self, p):
        self.lexer.state = self.lexer.EXPR_FNAME

    @pg.production("singleton_method_post_fname : ")
    def singleton_method_post_fname(self, p):
        self.lexer.state = self.lexer.EXPR_ENDFN

    @pg.production("primary : BREAK")
    def primary_break(self, p):
        return BoxAST(ast.Break(ast.Nil()))

    @pg.production("primary : NEXT")
    def primary_next(self, p):
        return BoxAST(ast.Next(ast.Nil()))

    @pg.production("primary : REDO")
    def primary_redo(self, p):
        """
        kREDO {
                    $$ = new RedoNode($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : RETRY")
    def primary_retry(self, p):
        """
        kRETRY {
                    $$ = new RetryNode($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary_value : primary")
    def primary_value(self, p):
        """
        primary {
                    support.checkExpression($1);
                    $$ = $1;
                    if ($$ == null) $$ = NilImplicitNode.NIL;
                }
        """
        # TODO: checkExpression, implicit Nil
        return p[0]

    @pg.production("then : term THEN")
    @pg.production("then : THEN")
    @pg.production("then : term")
    def then(self, p):
        return p[0]

    @pg.production("do : DO_COND")
    @pg.production("do : term")
    def do(self, p):
        return p[0]

    @pg.production("if_tail : opt_else")
    def if_tail_opt_else(self, p):
        return p[0]

    @pg.production("if_tail : ELSIF expr_value then compstmt if_tail")
    def if_tail_elsif(self, p):
        return BoxAST(ast.If(
            p[1].getast(),
            ast.Block(p[3].getastlist()),
            p[4].getast() if p[4] else ast.Nil(),
        ))

    @pg.production("opt_else : none")
    def opt_else_none(self, p):
        return p[0]

    @pg.production("opt_else : ELSE compstmt")
    def opt_else(self, p):
        return BoxAST(ast.Block(p[1].getastlist()) if p[1] is not None else ast.Nil())

    @pg.production("for_var : mlhs")
    @pg.production("for_var : lhs")
    def for_var(self, p):
        box = BoxForVars(p[0])
        self.lexer.symtable.declare_local(box.getargument().name)
        return box

    @pg.production("f_marg : f_norm_arg")
    def f_marg_f_norm_arg(self, p):
        return p[0]

    @pg.production("f_marg : LPAREN f_margs rparen")
    def f_marg_paren(self, p):
        return BoxAST(p[1].getassignment())

    @pg.production("f_marg_list : f_marg")
    def f_marg_list_f_marg(self, p):
        return self.new_list(p[0])

    @pg.production("f_marg_list : f_marg_list LITERAL_COMMA f_marg")
    def f_marg_list(self, p):
        return self.append_to_list(p[0], p[2])

    @pg.production("f_margs : f_marg_list")
    def f_margs_f_marg_list(self, p):
        return self._new_assignable_list(self.args_to_variables(p[0]))

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR f_norm_arg")
    def f_margs_f_marg_list_comma_star_f_norm_Arg(self, p):
        return self._new_assignable_list(self.args_to_variables(p[0]) + [ast.Splat(self.arg_to_variable(p[3]))])

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR f_norm_arg LITERAL_COMMA f_marg_list")
    def f_margs_f_marg_list_comma_star_f_norm_arg_comm_f_marg_list(self, p):
        return self._new_assignable_list(
            self.args_to_variables(p[0]) +
            [ast.Splat(self.arg_to_variable(p[3]))] +
            [self._arg_to_variable(node) for node in p[5].getastlist()]
        )

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR")
    def f_margs_f_marg_list_comma_star(self, p):
        return self._new_assignable_list(self.args_to_variables(p[0]) + [ast.Splat(None)])

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR LITERAL_COMMA f_marg_list")
    def f_margs_f_marg_list_comma_star_comma_f_marg_list(self, p):
        return self._new_assignable_list(
            self.args_to_variables(p[0]) +
            [ast.Splat(None)] +
            [self._arg_to_variable(node) for node in p[4].getastlist()]
        )

    @pg.production("f_margs : STAR f_norm_arg")
    def f_margs_star_f_norm_arg(self, p):
        return self._new_assignable_list([ast.Splat(self.arg_to_variable(p[1]))])

    @pg.production("f_margs : STAR f_norm_arg LITERAL_COMMA f_marg_list")
    def f_margs_star_f_norm_arg_comma_f_marg_list(self, p):
        return self._new_assignable_list(
            [ast.Splat(self.arg_to_variable(p[1]))] +
            [self._arg_to_variable(node) for node in p[3].getastlist()]
        )

    @pg.production("f_margs : STAR")
    def f_margs_star(self, p):
        return self._new_assignable_list([ast.Splat(None)])

    @pg.production("f_margs : STAR LITERAL_COMMA f_marg_list")
    def f_margs_star_comma_f_marg_list(self, p):
        return self._new_assignable_list(
            [ast.Splat(None)] +
            [self._arg_to_variable(node) for node in p[2].getastlist()]
        )

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        return self.new_args(
            args=self._new_list(p[0].getastlist() + p[2].getastlist()),
            splat_arg=p[4],
            block_arg=p[5]
        )

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        return self.new_args(
            args=self._new_list(p[0].getastlist() + p[2].getastlist()),
            splat_arg=p[4],
            block_arg=p[5]
        )

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_opt_f_block_arg(self, p):
        return self.new_args(self._new_list(p[0].getastlist() + p[2].getastlist()), None, p[3])

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_block_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, $5, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_arg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_rest_arg_opt_f_block_arg(self, p):
        return self.new_args(p[0], splat_arg=p[2], block_arg=p[3])

    @pg.production("block_param : f_arg LITERAL_COMMA")
    def block_param_f_arg_comma(self, p):
        self.lexer.symtable.declare_argument("*")
        tok = self.new_token(p[1], "IDENTIFIER", "*")
        return self.new_args(p[0], splat_arg=tok)

    @pg.production("block_param : f_arg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, $5, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_arg opt_f_block_arg")
    def block_param_f_arg_opt_f_block_arg(self, p):
        return self.new_args(p[0], block_arg=p[1])

    @pg.production("block_param : f_block_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def block_param_f_block_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        return self.new_args(p[0], splat_arg=p[2], block_arg=p[3])

    @pg.production("block_param : f_block_optarg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_block_optarg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_block_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, $3, $5, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_block_optarg opt_f_block_arg")
    def block_param_f_block_optarg_opt_f_block_arg(self, p):
        return self.new_args(p[0], None, p[1])

    @pg.production("block_param : f_block_optarg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_block_optarg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_block_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, null, $3, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_rest_arg opt_f_block_arg")
    def block_param_f_rest_arg_opt_f_block_arg(self, p):
        return self.new_args(splat_arg=p[0], block_arg=p[1])

    @pg.production("block_param : f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, $1, $3, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_block_arg")
    def block_param_f_block_arg(self, p):
        return self.new_args(block_arg=p[0])

    @pg.production("opt_block_param : none")
    def opt_block_param_none(self, p):
        return self.new_args()

    @pg.production("opt_block_param : block_param_def")
    def opt_block_param(self, p):
        self.lexer.command_start = True
        return p[0]

    @pg.production("block_param_def : PIPE opt_bv_decl PIPE")
    def block_param_def_pipe_opt_bv_decl_pipe(self, p):
        """
        tPIPE opt_bv_decl tPIPE {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param_def : OROP")
    def block_param_def_orop(self, p):
        return self.new_args()

    @pg.production("block_param_def : PIPE block_param opt_bv_decl PIPE")
    def block_param_def_pipe_block_param_opt_bv_decl_pipe(self, p):
        return p[1]

    @pg.production("opt_bv_decl : opt_nl")
    def opt_bv_decl_opt_nl(self, p):
        return None

    @pg.production("opt_bv_decl : opt_nl LITERAL_SEMICOLON bv_decls opt_nl")
    def opt_bv_decl(self, p):
        return None

    @pg.production("bv_decls : bvar")
    def bv_decls_bvar(self, p):
        return None

    @pg.production("bv_decls : bv_decls LITERAL_COMMA bvar")
    def bv_decls(self, p):
        return None

    @pg.production("bvar : IDENTIFIER")
    def bvar_identifier(self, p):
        """
        tIDENTIFIER {
                    support.new_bv($1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("bvar : f_bad_arg")
    def bvar_f_bad_arg(self, p):
        return None

    @pg.production("lambda : PRE_LAMBDA f_larglist lambda_body")
    def lambda_prod(self, p):
        self.lexer.left_paren_begin = p[0].getint()
        node = ast.SendBlock(
            p[1].getargs(),
            p[1].getsplatarg(),
            p[1].getblockarg(),
            ast.Block(p[2].getastlist()) if p[2] is not None else ast.Nil()
        )
        self.save_and_pop_scope(node)
        return BoxAST(ast.Lambda(node))

    @pg.production("PRE_LAMBDA :")
    def pre_lambda(self, p):
        self.push_block_scope()
        left_paren_begin = self.lexer.left_paren_begin
        self.lexer.paren_nest += 1
        self.lexer.left_paren_begin = self.lexer.paren_nest
        return BoxInt(left_paren_begin)

    @pg.production("f_larglist : LPAREN2 f_args opt_bv_decl RPAREN")
    def f_larglist_parens(self, p):
        return p[1]

    @pg.production("f_larglist : f_args opt_bv_decl")
    def f_larglist(self, p):
        return p[0]

    @pg.production("lambda_body : LAMBEG compstmt RCURLY")
    def lambda_body_lambeg(self, p):
        return p[1]

    @pg.production("lambda_body : DO_LAMBDA compstmt END")
    def lambda_body_do(self, p):
        return p[1]

    @pg.production("do_block : DO_BLOCK push_block_scope opt_block_param compstmt END")
    def do_block(self, p):
        box = self.new_send_block(p[0].getsourcepos().lineno, p[2], p[3])
        self.save_and_pop_scope(box.getast())
        return box

    @pg.production("push_block_scope : ")
    def push_block_scope_prod(self, p):
        self.push_block_scope()

    @pg.production("block_call : command do_block")
    def block_call_command_do_block(self, p):
        return self.combine_send_block(p[0], p[1])

    @pg.production("block_call : block_call DOT operation2 opt_paren_args")
    def block_call_dot_operation_opt_paren_args(self, p):
        """
        block_call tDOT operation2 opt_paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_call : block_call COLON2 operation2 opt_paren_args")
    def block_call_colon_operation_opt_paren_args(self, p):
        """
        block_call tCOLON2 operation2 opt_paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }

        """
        raise NotImplementedError(p)

    @pg.production("method_call : operation paren_args")
    def method_call_operation_paren_args(self, p):
        return self.new_fcall(p[0], p[1])

    @pg.production("method_call : primary_value DOT operation2 opt_paren_args")
    def method_call_primary_value_dot_operation_opt_paren_args(self, p):
        return self.new_call(p[0], p[2], p[3])

    @pg.production("method_call : primary_value COLON2 operation2 paren_args")
    def method_call_primary_value_colon_operation_paren_args(self, p):
        return self.new_call(p[0], p[2], p[3])

    @pg.production("method_call : primary_value COLON2 operation3")
    def method_call_primary_value_colon_operation(self, p):
        return self.new_call(p[0], p[2], None)

    @pg.production("method_call : primary_value DOT paren_args")
    def method_call_primary_value_dot_paren_args(self, p):
        return self.new_call(p[0], self.new_token(p[1], "call", "call"), p[2])

    @pg.production("method_call : primary_value COLON2 paren_args")
    def method_call_primary_value_colon_paren_args(self, p):
        return self.new_call(p[0], self.new_token(p[1], "call", "call"), p[2])

    @pg.production("method_call : SUPER paren_args")
    def method_call_super_paren_args(self, p):
        return self.new_super(p[1], p[0])

    @pg.production("method_call : SUPER")
    def method_call_super(self, p):
        lineno = p[0].getsourcepos().lineno
        args = []
        for n, tp in self.lexer.symtable.arguments:
            if tp == self.lexer.symtable.BLOCK_ARG:
                continue
            node = ast.Variable(n, lineno)
            if tp == self.lexer.symtable.SPLAT_ARG:
                node = ast.Splat(node)
            args.append(node)
        return BoxAST(ast.Super(args, None, lineno))

    @pg.production("method_call : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def method_call_primary_value_lbracket_opt_call_args_rbracket(self, p):
        return self.new_call(p[0], self.new_token(p[1], "[]", "[]"), p[2])

    @pg.production("brace_block : LCURLY push_block_scope opt_block_param compstmt RCURLY")
    def brace_block_curly(self, p):
        box = self.new_send_block(p[0].getsourcepos().lineno, p[2], p[3])
        self.save_and_pop_scope(box.getast())
        return box

    @pg.production("brace_block : DO push_block_scope opt_block_param compstmt END")
    def brace_block_do(self, p):
        box = self.new_send_block(p[0].getsourcepos().lineno, p[2], p[3])
        self.save_and_pop_scope(box.getast())
        return box

    @pg.production("case_body : WHEN args then compstmt cases")
    def case_body(self, p):
        body = ast.Block(p[3].getastlist()) if p[3] is not None else ast.Nil()
        items = [
            ast.When(p[1].getcallargs(), body, p[0].getsourcepos().lineno)
        ]
        items.extend(p[4].getastlist())
        return self._new_list(items)

    @pg.production("cases : opt_else")
    def cases_opt_else(self, p):
        body = p[0].getast() if p[0] is not None else ast.Nil()
        # TODO: a real line number here
        return self.new_list(BoxAST(ast.When(None, body, -1)))

    @pg.production("cases : case_body")
    def cases_case_body(self, p):
        return p[0]

    @pg.production("opt_rescue : RESCUE exc_list exc_var then compstmt opt_rescue")
    def opt_rescue(self, p):
        handlers = [
            ast.ExceptHandler(
                p[1].getastlist() if p[1] is not None else [],
                p[2].getast() if p[2] is not None else None,
                ast.Block(p[4].getastlist()) if p[4] is not None else ast.Nil(),
            )
        ]
        if p[5] is not None:
            handlers.extend(p[5].getastlist())
        return BoxASTList(handlers)

    @pg.production("opt_rescue : ")
    def opt_rescue_empty(self, p):
        return None

    @pg.production("exc_list : arg_value")
    def exc_list_arg_value(self, p):
        return self.new_list(p[0])

    @pg.production("exc_list : mrhs")
    def exc_list_mrhs(self, p):
        return p[0]

    @pg.production("exc_list : none")
    def exc_list_none(self, p):
        return p[0]

    @pg.production("exc_var  : ASSOC lhs")
    def exc_var(self, p):
        return p[1]

    @pg.production("exc_var : none")
    def exc_var_none(self, p):
        return p[0]

    @pg.production("opt_ensure : ENSURE compstmt")
    def opt_ensure(self, p):
        return p[1]

    @pg.production("opt_ensure : none")
    def opt_ensure_none(self, p):
        return p[0]

    @pg.production("literal : numeric")
    def literal_numeric(self, p):
        return p[0]

    @pg.production("literal : symbol")
    def literal_symbol(self, p):
        return self.new_symbol(p[0])

    @pg.production("literal : dsym")
    def literal_dsym(self, p):
        return p[0]

    @pg.production("strings : string")
    def strings(self, p):
        return p[0]

    @pg.production("string : CHAR")
    def string_char(self, p):
        # TODO: encoding
        return BoxAST(ast.ConstantString(p[0].getstr()))

    @pg.production("string : string1")
    def string_string1(self, p):
        return p[0]

    @pg.production("string : string string1")
    def string_string_string1(self, p):
        return self.concat_literals(p[0], p[1])

    @pg.production("string1 : STRING_BEG string_contents STRING_END")
    def string1(self, p):
        return p[1]

    @pg.production("xstring : XSTRING_BEG xstring_contents STRING_END")
    def xstring(self, p):
        return self.new_fcall(self.new_token(p[0], "`", "`"), self.new_call_args(p[1]))

    @pg.production("regexp : REGEXP_BEG xstring_contents REGEXP_END")
    def regexp(self, p):
        str_flags = p[2].getstr()
        flags = 0
        for f in str_flags:
            flags |= regexp.OPTIONS_MAP[f]
        if p[1] is not None:
            n = p[1].getast()
            if isinstance(n, ast.ConstantString):
                node = ast.ConstantRegexp(n.strvalue, flags, p[0].getsourcepos().lineno)
            else:
                node = ast.DynamicRegexp(n, flags)
        else:
            node = ast.ConstantRegexp("", flags, p[0].getsourcepos().lineno)
        return BoxAST(node)

    @pg.production("words : WORDS_BEG LITERAL_SPACE STRING_END")
    def words_space(self, p):
        """
        tWORDS_BEG ' ' tSTRING_END {
                    $$ = new ZArrayNode($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("words : WORDS_BEG word_list STRING_END")
    def words_word_list(self, p):
        return BoxAST(ast.Array(p[1].getastlist()))

    @pg.production("word_list : ")
    def word_list_empty(self, p):
        return self.new_list()

    @pg.production("word_list : word_list word LITERAL_SPACE")
    def word_list(self, p):
        return self.append_to_list(p[0], p[1])

    @pg.production("word : string_content")
    def word_string_content(self, p):
        return p[0]

    @pg.production("word : word string_content")
    def word(self, p):
        """
        word string_content {
                     $$ = support.literal_concat(support.getPosition($1), $1, $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("qwords : QWORDS_BEG LITERAL_SPACE STRING_END")
    def qwords_space(self, p):
        return BoxAST(ast.Array([]))

    @pg.production("qwords : QWORDS_BEG qword_list STRING_END")
    def qwords_qword_list(self, p):
        return BoxAST(ast.Array(p[1].getastlist()))

    @pg.production("qword_list : ")
    def qword_list_empty(self, p):
        return self.new_list()

    @pg.production("qword_list : qword_list STRING_CONTENT LITERAL_SPACE")
    def qword_list(self, p):
        return self.append_to_list(p[0], BoxAST(ast.ConstantString(p[1].getstr())))

    @pg.production("string_contents : ")
    def string_contents_empty(self, p):
        # TODO: Encoding?
        return BoxAST(ast.ConstantString(""))

    @pg.production("string_contents : string_contents string_content")
    def string_contents(self, p):
        return self.concat_literals(p[0], p[1])

    @pg.production("xstring_contents : ")
    def xstring_contents_empty(self, p):
        return None

    @pg.production("xstring_contents : xstring_contents string_content")
    def xstring_contents(self, p):
        return self.concat_literals(p[0], p[1])

    @pg.production("string_content : STRING_CONTENT")
    def string_content_string_content(self, p):
        return BoxAST(ast.ConstantString(p[0].getstr()))

    @pg.production("string_content : string_dvar_prod string_dvar")
    def string_content_string_dvar(self, p):
        self.lexer.str_term = p[0].getstrterm()
        return p[1]

    @pg.production("string_dvar_prod : STRING_DVAR")
    def string_dvar_prod(self, p):
        str_term = self.lexer.str_term
        self.lexer.str_term = None
        self.lexer.state = self.lexer.EXPR_BEG
        return BoxStrTerm(str_term)

    @pg.production("string_content : string_dbeg compstmt RCURLY")
    def string_content_string_dbeg(self, p):
        self.lexer.condition_state.restart()
        self.lexer.cmd_argument_state.restart()
        self.lexer.str_term = p[0].getstrterm()
        if p[1]:
            return BoxAST(ast.DynamicString([ast.Block(p[1].getastlist())]))
        else:
            return None

    @pg.production("string_dbeg : STRING_DBEG")
    def string_dbeg(self, p):
        str_term = self.lexer.str_term
        self.lexer.condition_state.stop()
        self.lexer.cmd_argument_state.stop()
        self.lexer.str_term = None
        self.lexer.state = self.lexer.EXPR_BEG
        return BoxStrTerm(str_term)

    @pg.production("string_dvar : GVAR")
    def string_dvar_gvar(self, p):
        return self.new_global(p[0])

    @pg.production("string_dvar : IVAR")
    def string_dvar_ivar(self, p):
        return self.new_instance_var(p[0])

    @pg.production("string_dvar : CVAR")
    def string_dvar_cvar(self, p):
        return self.new_class_var(p[0])

    @pg.production("string_dvar : backref")
    def string_dvar_backref(self, p):
        return p[0]

    @pg.production("symbol : SYMBEG sym")
    def symbol(self, p):
        self.lexer.state = self.lexer.EXPR_END
        return p[1]

    @pg.production("sym : CVAR")
    @pg.production("sym : GVAR")
    @pg.production("sym : IVAR")
    @pg.production("sym : fname")
    def sym(self, p):
        return p[0]

    @pg.production("dsym : SYMBEG xstring_contents STRING_END")
    def dsym(self, p):
        box = p[1]
        if box is None:
            return BoxAST(ast.ConstantSymbol(""))
        node = box.getast()
        if isinstance(node, ast.ConstantString):
            return BoxAST(ast.ConstantSymbol(node.strvalue))
        else:
            return BoxAST(ast.Symbol(node, p[0].getsourcepos().lineno))

    @pg.production("numeric : INTEGER")
    def numeric_integer(self, p):
        return BoxAST(self._parse_int(p[0]))

    @pg.production("numeric : FLOAT")
    def numeric_float(self, p):
        return BoxAST(ast.ConstantFloat(float(p[0].getstr())))

    @pg.production("numeric : UMINUS_NUM INTEGER", precedence="LOWEST")
    def numeric_minus_integer(self, p):
        return BoxAST(self._parse_int(p[1]).negate())

    @pg.production("numeric : UMINUS_NUM FLOAT", precedence="LOWEST")
    def numeric_minus_float(self, p):
        return BoxAST(ast.ConstantFloat(-float(p[1].getstr())))

    @pg.production("user_variable : IDENTIFIER")
    def variable_identifier(self, p):
        return BoxAST(ast.Variable(p[0].getstr(), p[0].getsourcepos().lineno))

    @pg.production("user_variable : IVAR")
    def variable_ivar(self, p):
        return self.new_instance_var(p[0])

    @pg.production("user_variable : GVAR")
    def variable_gvar(self, p):
        return self.new_global(p[0])

    @pg.production("user_variable : CONSTANT")
    def variable_constant(self, p):
        return BoxAST(ast.Constant(
            p[0].getstr(),
            p[0].getsourcepos().lineno
        ))

    @pg.production("user_variable : CVAR")
    def variable_cvar(self, p):
        return self.new_class_var(p[0])

    @pg.production("keyword_variable : NIL")
    def variable_nil(self, p):
        return BoxAST(ast.Nil())

    @pg.production("keyword_variable : SELF")
    def variable_self(self, p):
        return BoxAST(ast.Self(p[0].getsourcepos().lineno))

    @pg.production("keyword_variable : TRUE")
    def variable_true(self, p):
        return BoxAST(ast.ConstantBool(True))

    @pg.production("keyword_variable : FALSE")
    def variable_false(self, p):
        return BoxAST(ast.ConstantBool(False))

    @pg.production("keyword_variable : __FILE__")
    def variable__file__(self, p):
        return BoxAST(ast.File())

    @pg.production("keyword_variable : __LINE__")
    def variable__line__(self, p):
        return BoxAST(ast.Line(p[0].getsourcepos().lineno))

    @pg.production("keyword_variable : __ENCODING__")
    def variable__encoding__(self, p):
        raise NotImplementedError(p)
        return BoxAST(ast.Encoding())

    @pg.production("var_ref : keyword_variable")
    @pg.production("var_ref : user_variable")
    def var_ref(self, p):
        node = p[0].getast()
        if isinstance(node, ast.Variable):
            if self.lexer.symtable.is_defined(node.name):
                self.lexer.symtable.declare_read(node.name)
                return p[0]
            else:
                return BoxAST(ast.Send(ast.Self(node.lineno), node.name, [], None, node.lineno))
        else:
            return p[0]

    @pg.production("var_lhs : user_variable")
    @pg.production("var_lhs : keyword_variable")
    def var_lhs(self, p):
        return self.assignable(p[0])

    @pg.production("backref : BACK_REF")
    @pg.production("backref : NTH_REF")
    def backref(self, p):
        return p[0]

    @pg.production("superclass : term")
    def superclass_term(self, p):
        return None

    @pg.production("superclass : superclass_lt expr_value term")
    def superclass(self, p):
        return p[1]

    @pg.production("superclass_lt : LT")
    def superclass_lt(self, p):
        self.lexer.state = self.lexer.EXPR_BEG

    @pg.production("superclass : error term")
    def superclass_error(self, p):
        return None

    @pg.production("f_arglist : LPAREN2 f_args rparen")
    def f_arglist_parens(self, p):
        self.lexer.state = self.lexer.EXPR_BEG
        self.lexer.command_start = True
        return p[1]

    @pg.production("f_arglist : f_args term")
    def f_arglist(self, p):
        self.lexer.state = self.lexer.EXPR_BEG
        self.lexer.command_start = True
        return p[0]

    @pg.production("f_args : f_arg LITERAL_COMMA f_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def f_args_f_arg_comma_f_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        return self.new_args(
            self._new_list(p[0].getastlist() + p[2].getastlist()),
            splat_arg=p[4],
            block_arg=p[5],
        )

    @pg.production("f_args : f_arg LITERAL_COMMA f_optarg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_arg_comma_f_optarg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, $7, $8);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_arg LITERAL_COMMA f_optarg opt_f_block_arg")
    def f_args_f_arg_comma_f_optarg_opt_f_block_arg(self, p):
        return self.new_args(
            self._new_list(p[0].getastlist() + p[2].getastlist()),
            block_arg=p[3],
        )

    @pg.production("f_args : f_arg LITERAL_COMMA f_optarg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_arg_comma_f_optarg_comma_f_arg_opt_f_block_arg(self, p):
        return self.new_args(
            self._new_list(p[0].getastlist() + p[2].getastlist() + p[4].getastlist()),
            block_arg=p[5],
        )

    @pg.production("f_args : f_arg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def f_args_f_arg_comma_f_rest_arg_opt_f_block_arg(self, p):
        return self.new_args(
            p[0],
            splat_arg=p[2],
            block_arg=p[3],
        )

    @pg.production("f_args : f_arg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_arg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, $5, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_arg opt_f_block_arg")
    def f_args_f_arg_opt_f_block_arg(self, p):
        return self.new_args(p[0], block_arg=p[1])

    @pg.production("f_args : f_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def f_args_f_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        return self.new_args(p[0], splat_arg=p[2], block_arg=p[3])

    @pg.production("f_args : f_optarg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_optarg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, $3, $5, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_optarg opt_f_block_arg")
    def f_args_f_optarg_opt_f_block_arg(self, p):
        return self.new_args(p[0], block_arg=p[1])

    @pg.production("f_args : f_optarg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_optarg_comma_f_arg_opt_f_block_arg(self, p):
        return self.new_args(
            self._new_list(p[0].getastlist() + p[2].getastlist()),
            block_arg=p[3]
        )

    @pg.production("f_args : f_rest_arg opt_f_block_arg")
    def f_args_f_rest_arg_opt_f_block_arg(self, p):
        return self.new_args(splat_arg=p[0], block_arg=p[1])

    @pg.production("f_args : f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        self.lexer.symtable.declare_argument("2", self.lexer.symtable.SPLAT_ARG)
        splat = ast.Splat(ast.Variable(p[0].getstr(), -1))
        assignable = self._new_assignable_list([splat] + self.args_to_variables(p[2]))
        return BoxArgs([assignable.getassignment()], "2", p[3].getstr() if p[3] is not None else None)

    @pg.production("f_args : f_block_arg")
    def f_args_f_block_arg(self, p):
        return self.new_args(block_arg=p[0])

    @pg.production("f_args : ")
    def f_args_none(self, p):
        return self.new_args()

    @pg.production("f_bad_arg : CONSTANT")
    def f_bad_arg_constant(self, p):
        raise self.error("formal argument cannot be a constant")

    @pg.production("f_bad_arg : IVAR")
    def f_bad_arg_ivar(self, p):
        raise self.error("formal argument cannot be an instance variable")

    @pg.production("f_bad_arg : GVAR")
    def f_bad_arg_gvar(self, p):
        raise self.error("formal argument cannot be a global variable")

    @pg.production("f_bad_arg : CVAR")
    def f_bad_arg_cvar(self, p):
        raise self.error("formal argument cannot be a class variable")

    @pg.production("f_norm_arg : f_bad_arg")
    def f_norm_arg_f_bad_arg(self, p):
        return p[0]

    @pg.production("f_norm_arg : IDENTIFIER")
    def f_norm_arg_identifier(self, p):
        return BoxAST(ast.Argument(p[0].getstr()))

    @pg.production("f_arg_item : f_norm_arg")
    def f_arg_item_f_norm_arg(self, p):
        node = p[0].getast(ast.Argument)
        self.lexer.symtable.declare_argument(node.name)
        return p[0]

    @pg.production("f_arg_item : LPAREN f_margs rparen")
    def f_arg_item_paren(self, p):
        return BoxAST(p[1].getassignment())

    @pg.production("f_arg : f_arg_item")
    def f_arg_f_arg_item(self, p):
        return self.new_list(p[0])

    @pg.production("f_arg : f_arg LITERAL_COMMA f_arg_item")
    def f_arg(self, p):
        return self.append_to_list(p[0], p[2])

    @pg.production("f_opt : IDENTIFIER LITERAL_EQUAL arg_value")
    def f_opt(self, p):
        self.lexer.symtable.declare_argument(p[0].getstr())
        return BoxAST(ast.Argument(p[0].getstr(), p[2].getast()))

    @pg.production("f_block_opt : IDENTIFIER LITERAL_EQUAL primary_value")
    def f_block_opt(self, p):
        self.lexer.symtable.declare_argument(p[0].getstr())
        return BoxAST(ast.Argument(p[0].getstr(), p[2].getast()))

    @pg.production("f_block_optarg : f_block_opt")
    def f_block_optarg_f_block_opt(self, p):
        return self.new_list(p[0])

    @pg.production("f_block_optarg : f_block_optarg LITERAL_COMMA f_block_opt")
    def f_block_optarg(self, p):
        return self.append_to_list(p[0], p[2])

    @pg.production("f_optarg : f_opt")
    def f_optarg_f_opt(self, p):
        return self.new_list(p[0])

    @pg.production("f_optarg : f_optarg LITERAL_COMMA f_opt")
    def f_optarg(self, p):
        return self.append_to_list(p[0], p[2])

    @pg.production("restarg_mark : STAR")
    @pg.production("restarg_mark : STAR2")
    def restarg_mark(self, p):
        return p[0]

    @pg.production("f_rest_arg : restarg_mark IDENTIFIER")
    def f_rest_arg_restarg_mark_identifer(self, p):
        self.lexer.symtable.declare_argument(p[1].getstr(), self.lexer.symtable.SPLAT_ARG)
        return p[1]

    @pg.production("f_rest_arg : restarg_mark")
    def f_rest_arg_restarg_mark(self, p):
        self.lexer.symtable.declare_argument("*", self.lexer.symtable.SPLAT_ARG)
        return self.new_token(p[0], "IDENTIFIER", "*")

    @pg.production("blkarg_mark : AMPER")
    @pg.production("blkarg_mark : AMPER2")
    def blkarg_mark(self, p):
        return p[0]

    @pg.production("f_block_arg : blkarg_mark IDENTIFIER")
    def f_block_arg(self, p):
        self.lexer.symtable.declare_argument(p[1].getstr(), self.lexer.symtable.BLOCK_ARG)
        return p[1]

    @pg.production("opt_f_block_arg : LITERAL_COMMA f_block_arg")
    def opt_f_block_arg(self, p):
        return p[1]

    @pg.production("opt_f_block_arg : ")
    def opt_f_block_arg_empty(self, p):
        return None

    @pg.production("singleton : var_ref")
    def singleton_var_ref(self, p):
        return p[0]

    @pg.production("singleton : LPAREN expr rparen")
    def singleton_paren(self, p):
        """
        tLPAREN2 {
                    lexer.setState(LexState.EXPR_BEG);
                } expr rparen {
                    if ($3 == null) {
                        support.yyerror("can't define single method for ().");
                    } else if ($3 instanceof ILiteralNode) {
                        support.yyerror("can't define single method for literals.");
                    }
                    support.checkExpression($3);
                    $$ = $3;
                }
        """
        raise NotImplementedError(p)

    @pg.production("assoc_list : none")
    def assoc_list_none(self, p):
        return self.new_list()

    @pg.production("assoc_list : assocs trailer")
    def assoc_list(self, p):
        return p[0]

    @pg.production("assocs : assoc")
    def assocs_assoc(self, p):
        return p[0]

    @pg.production("assocs : assocs LITERAL_COMMA assoc")
    def assocs(self, p):
        return self._new_list(p[0].getastlist() + p[2].getastlist())

    @pg.production("assoc : arg_value ASSOC arg_value")
    def assoc_arg_value(self, p):
        return self.append_to_list(self.new_list(p[0]), p[2])

    @pg.production("assoc : LABEL arg_value")
    def assoc_label(self, p):
        return self.append_to_list(self.new_list(self.new_symbol(p[0])), p[1])

    @pg.production("operation : FID")
    @pg.production("operation : CONSTANT")
    @pg.production("operation : IDENTIFIER")
    def operation(self, p):
        return p[0]

    @pg.production("operation2 : op")
    @pg.production("operation2 : FID")
    @pg.production("operation2 : CONSTANT")
    @pg.production("operation2 : IDENTIFIER")
    def operation2(self, p):
        return p[0]

    @pg.production("operation3 : op")
    @pg.production("operation3 : FID")
    @pg.production("operation3 : IDENTIFIER")
    def operation3(self, p):
        return p[0]

    @pg.production("dot_or_colon : COLON2")
    @pg.production("dot_or_colon : DOT")
    def dot_or_colon(self, p):
        return p[0]

    @pg.production("opt_terms : ")
    def opt_terms_none(self, p):
        return None

    @pg.production("opt_terms : terms")
    def opt_terms(self, p):
        return p[0]

    @pg.production("opt_nl : ")
    def opt_nl_none(self, p):
        return None

    @pg.production("opt_nl : LITERAL_NEWLINE")
    def opt_nl(self, p):
        return None

    @pg.production("rparen : opt_nl RPAREN")
    def rparen(self, p):
        return p[1]

    @pg.production("rbracket : opt_nl RBRACK")
    def rbracket(self, p):
        return p[1]

    @pg.production("trailer : ")
    def trailer_none(self, p):
        return None

    @pg.production("trailer : LITERAL_COMMA")
    @pg.production("trailer : LITERAL_NEWLINE")
    def trailer(self, p):
        return p[0]

    @pg.production("term : LITERAL_NEWLINE")
    @pg.production("term : LITERAL_SEMICOLON")
    def term(self, p):
        return p[0]

    @pg.production("terms : term")
    def terms_term(self, p):
        return p[0]

    @pg.production("terms : terms LITERAL_SEMICOLON")
    def terms(self, p):
        return p[0]

    @pg.production("none : ")
    def none(self, p):
        return None

    @pg.production("none_block_pass : ")
    def none_block_pass(self, p):
        return None

    parser = pg.build()


class LexerWrapper(object):
    def __init__(self, lexer):
        self.lexer = lexer

    def next(self):
        try:
            return self.lexer.next()
        except StopIteration:
            return None


class BoxAST(BaseBox):
    def __init__(self, node):
        self.node = node

    @specialize.arg(1)
    def getast(self, cls=None):
        node = self.node
        if cls is not None:
            assert isinstance(node, cls)
        return node


class BoxASTList(BaseBox):
    def __init__(self, nodes):
        self.nodes = nodes

    def getastlist(self):
        return self.nodes


class BoxCallArgs(BaseBox):
    """
    A box for the arguments of a call/send.
    """
    def __init__(self, args, block):
        self.args = args
        self.block = block

    def getcallargs(self):
        return self.args

    def getcallblock(self):
        return self.block


class BoxInt(BaseBox):
    def __init__(self, intvalue):
        self.intvalue = intvalue

    def getint(self):
        return self.intvalue


class BoxArgs(BaseBox):
    """
    A box for the arguments of a function/block definition.
    """
    def __init__(self, args, splat_arg, block_arg):
        self.args = args
        self.splat_arg = splat_arg
        self.block_arg = block_arg

    def getargs(self, include_multi=False):
        if self.is_multiassignment() and not include_multi:
            return []
        else:
            return self.args

    def getsplatarg(self):
        return self.splat_arg

    def getblockarg(self):
        return self.block_arg

    def is_multiassignment(self):
        return len(self.args) == 1 and isinstance(self.args[0], ast.MultiAssignable)

    def getfullbody(self, block):
        if self.is_multiassignment():
            prebody = ast.Statement(ast.MultiAssignment(self.args[0], ast.Variable("2", -1)))
            if isinstance(block, ast.Nil):
                return ast.Block([prebody])
            elif isinstance(block, ast.Block):
                return ast.Block([prebody] + block.stmts)
            else:
                raise SystemError
        else:
            return block


class BoxStrTerm(BaseBox):
    def __init__(self, str_term):
        self.str_term = str_term

    def getstrterm(self):
        return self.str_term


class BoxAssignableList(BaseBox):
    def __init__(self, vars):
        self.vars = vars

    def getassignment(self):
        return ast.MultiAssignable(self.vars)

    def getvars(self):
        return self.vars


class BoxForVars(BaseBox):
    def __init__(self, for_var):
        self.for_var = for_var
        self.argument = ast.Argument("0")

    def getargument(self):
        return self.argument

    def get_for_var(self):
        return self.for_var
