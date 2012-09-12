from rply import ParserGenerator, Token
from rply.token import BaseBox

from rupypy import ast


class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer

    def parse(self):
        l = LexerWrapper(self.lexer.tokenize())
        return self.parser.parse(l, state=self)

    def new_token(self, orig, name):
        return Token(name, name, orig.getsourcepos())

    def new_list(self, box):
        return BoxASTList([box.getast()])

    def append_to_list(self, box_list, box):
        return BoxASTList(box_list.getastlist() + [box.getast()])

    def new_stmt(self, box):
        return BoxAST(ast.Statement(box.getast()))

    def new_binary_call(self, lhs, op, rhs):
        return self._new_call(lhs.getast(), op, [rhs.getast()])

    def new_call(self, receiver, method, args):
        args = args.getargs() if args is not None else []
        return self._new_call(receiver.getast(), method, args)

    def new_fcall(self, method, args):
        receiver = ast.Self(method.getsourcepos().lineno)
        return self._new_call(receiver, method, args.getargs())

    def _new_call(self, receiver, method, args):
        return BoxAST(ast.Send(receiver, method.getstr(), args, None, method.getsourcepos().lineno))

    def new_and(self, lhs, rhs):
        return BoxAST(ast.And(lhs.getast(), rhs.getast()))

    def new_or(self, lhs, rhs):
        return BoxAST(ast.Or(lhs.getast(), rhs.getast()))

    def new_args(self, box_arg):
        return self._new_args([box_arg.getast()], None)

    def _new_args(self, args, block):
        return BoxArgs(args, block)

    def arg_block_pass(self, box_args, box_block_pass):
        if box_block_pass is None:
            return box_args
        return self._new_args(box_args.getargs(), box_block_pass.getast())

    def append_arg(self, box_arg, box):
        return self._new_args(box_arg.getargs() + [box.getast()], box_arg.getblock())

    def new_splat(self, box):
        return BoxAST(ast.Splat(box.getast()))

    def new_colon2(self, box, constant):
        return BoxAST(ast.LookupConstant(box.getast(), constant.getstr(), constant.getsourcepos().lineno))

    def new_colon3(self, constant):
        return BoxAST(ast.LookupConstant(None, constant.getstr(), constant.getsourcepos().lineno))

    def new_symbol(self, token):
        return BoxAST(ast.ConstantSymbol(token.getstr()))

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
                    dynamic = False
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
    ])

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
        return BoxAST(ast.Main(ast.Block(p[0].getastlist())))

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
        """
        bodystmt      : compstmt opt_rescue opt_else opt_ensure {
                  Node node = $1;

                  if ($2 != null) {
                      node = new RescueNode(support.getPosition($1), $1, $2, $3);
                  } else if ($3 != null) {
                      support.warn(ID.ELSE_WITHOUT_RESCUE, support.getPosition($1), "else without rescue is useless");
                      node = support.appendToBlock($1, $3);
                  }
                  if ($4 != null) {
                      if (node == null) node = NilImplicitNode.NIL;
                      node = new EnsureNode(support.getPosition($1), node, $4);
                  }

                  $$ = node;
                }
        """
        raise NotImplementedError(p)

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
        """
        kUNDEF undef_list {
                    $$ = $2;
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : stmt IF_MOD expr_value")
    def stmt_ifmod(self, p):
        """
        stmt kIF_MOD expr_value {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($3), $1, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : stmt UNLESS_MOD expr_value")
    def stmt_unlessmod(self, p):
        """
        stmt kUNLESS_MOD expr_value {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($3), null, $1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : stmt WHILE_MOD expr_value")
    def stmt_while_mod(self, p):
        """
        stmt kWHILE_MOD expr_value {
                    if ($1 != null && $1 instanceof BeginNode) {
                        $$ = new WhileNode(support.getPosition($1), support.getConditionNode($3), $<BeginNode>1.getBodyNode(), false);
                    } else {
                        $$ = new WhileNode(support.getPosition($1), support.getConditionNode($3), $1, true);
                    }
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : stmt UNTIL_MOD expr_value")
    def stmt_until_mod(self, p):
        """
        stmt kUNTIL_MOD expr_value {
                    if ($1 != null && $1 instanceof BeginNode) {
                        $$ = new UntilNode(support.getPosition($1), support.getConditionNode($3), $<BeginNode>1.getBodyNode(), false);
                    } else {
                        $$ = new UntilNode(support.getPosition($1), support.getConditionNode($3), $1, true);
                    }
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : stmt RESCUE_MOD stmt")
    def stmt_rescue_mod(self, p):
        """
        stmt kRESCUE_MOD stmt {
                    Node body = $3 == null ? NilImplicitNode.NIL : $3;
                    $$ = new RescueNode(support.getPosition($1), $1, new RescueBodyNode(support.getPosition($1), null, body, null), null);
                }
        """
        raise NotImplementedError(p)

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
        return p[0]

    @pg.production("stmt : mlhs LITERAL_EQUAL command_call")
    def stmt_mlhs_equal_command_call(self, p):
        """
        mlhs '=' command_call {
                    support.checkExpression($3);
                    $1.setValueNode($3);
                    $$ = $1;
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : var_lhs OP_ASGN command_call")
    def stmt_var_lhs_op_asgn_command_call(self, p):
        """
        var_lhs tOP_ASGN command_call {
                    support.checkExpression($3);

                    ISourcePosition pos = $1.getPosition();
                    String asgnOp = (String) $2.getValue();
                    if (asgnOp.equals("||")) {
                        $1.setValueNode($3);
                        $$ = new OpAsgnOrNode(pos, support.gettable2($1), $1);
                    } else if (asgnOp.equals("&&")) {
                        $1.setValueNode($3);
                        $$ = new OpAsgnAndNode(pos, support.gettable2($1), $1);
                    } else {
                        $1.setValueNode(support.getOperatorCallNode(support.gettable2($1), asgnOp, $3));
                        $1.setPosition(pos);
                        $$ = $1;
                    }
                }
        """
        raise NotImplementedError(p)

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
        self.backref_assign_error(p[0])

    @pg.production("stmt : lhs LITERAL_EQUAL mrhs")
    def stmt_lhs_equal_mrhs(self, p):
        """
        lhs '=' mrhs {
                    $$ = support.node_assign($1, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : mlhs LITERAL_EQUAL arg_value")
    def stmt_mlhs_equal_arg_value(self, p):
        """
        mlhs '=' arg_value {
                    $1.setValueNode($3);
                    $$ = $1;
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : mlhs LITERAL_EQUAL mrhs")
    def stmt_mlhs_equal_mrhs(self, p):
        """
        mlhs '=' mrhs {
                    $<AssignableNode>1.setValueNode($3);
                    $$ = $1;
                    $1.setPosition(support.getPosition($1));
                }
        """
        raise NotImplementedError(p)

    @pg.production("stmt : expr")
    def stmt_expr(self, p):
        return self.new_stmt(p[0])

    @pg.production("command_asgn : lhs LITERAL_EQUAL command_call")
    def command_asgn_lhs_equal_command_call(self, p):
        """
        lhs '=' command_call {
                    support.checkExpression($3);
                    $$ = support.node_assign($1, $3);
                }
        """
        raise NotImplementedError(p)

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
        return BoxAST(ast.Not(p[2].getast()))

    @pg.production("expr : BANG command_call")
    def expr_bang_command_call(self, p):
        return BoxAST(ast.Not(p[2].getast()))

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

    @pg.production("command_call : RETURN call_args")
    def command_call_return(self, p):
        return self.new_return(p[1])

    @pg.production("command_call : BREAK call_args")
    def command_call_break(self, p):
        return self.new_break(self, p[1])

    @pg.production("command_call : NEXT call_args")
    def command_call_next(self, p):
        return self.new_next(p[1])

    @pg.production("block_command : block_call")
    def block_command_block_call(self, p):
        return p[0]

    @pg.production("block_command : block_call DOT operation2 command_args")
    def block_command_dot(self, p):
        """
        block_call tDOT operation2 command_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_command : block_call COLON2 operation2 command_args")
    def block_command_colon(self, p):
        """
        block_call tCOLON2 operation2 command_args {
                    $$ = support.new_call($1, $3, $4, null);
                }

        """
        raise NotImplementedError(p)

    @pg.production("cmd_brace_block : LBRACE_ARG opt_block_param compstmt RCURLY")
    def cmd_brace_block(self, p):
        """
        tLBRACE_ARG {
                    support.pushBlockScope();
                } opt_block_param compstmt tRCURLY {
                    $$ = new IterNode($1.getPosition(), $3, $4, support.getCurrentScope());
                    support.popCurrentScope();
                }
        """
        raise NotImplementedError(p)

    @pg.production("command : operation command_args", precedence="LOWEST")
    def command_operation_command_args(self, p):
        return self.new_fcall(p[0], p[1])

    @pg.production("command : operation command_args cmd_brace_block")
    def command_operation_command_args_cmd_brace_block(self, p):
        """
        operation command_args cmd_brace_block {
                    $$ = support.new_fcall($1, $2, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("command : primary_value DOT operation2 command_args", precedence="LOWEST")
    def command_method_call_args(self, p):
        return self.new_call(p[0], p[2], p[3])

    @pg.production("command : primary_value DOT operation2 command_args cmd_brace_block")
    def command_method_call_args_brace_block(self, p):
        """
        primary_value tDOT operation2 command_args cmd_brace_block {
                    $$ = support.new_call($1, $3, $4, $5);
                }
        """
        raise NotImplementedError(p)

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
        return self.new_super(p[1])

    @pg.production("command : YIELD command_args")
    def command_yield(self, p):
        return self.new_yield(p[1])

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
        """
        mlhs_head {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, null, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : mlhs_head mlhs_item")
    def mlhs_basic_mlhs_head_mlhs_item(self, p):
        """
        mlhs_head mlhs_item {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1.add($2), null, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : mlhs_head STAR mlhs_node")
    def mlhs_basic_mlhs_head_star_node(self, p):
        """
        mlhs_head tSTAR mlhs_node {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, $3, (ListNode) null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : mlhs_head STAR mlhs_node LITERAL_COMMA mlhs_post")
    def mlhs_basic_mlhs_head_star_node_comma_post(self, p):
        """
        mlhs_head tSTAR mlhs_node ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, $3, $5);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : mlhs_head STAR")
    def mlhs_basic_mlhs_head_star(self, p):
        """
        mlhs_head tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : mlhs_head STAR LITERAL_COMMA mlhs_post")
    def mlhs_basic_mlhs_head_star_comma_post(self, p):
        """
        mlhs_head tSTAR ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : STAR mlhs_node")
    def mlhs_basic_star_mlhs_node(self, p):
        """
        tSTAR mlhs_node {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, $2, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : STAR mlhs_node LITERAL_COMMA mlhs_post")
    def mlhs_basic_star_mlhs_node_comma_post(self, p):
        """
        tSTAR mlhs_node ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, $2, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_basic : STAR")
    def mlhs_basic_star(self, p):
        """
        tSTAR {
                      $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), null);
                }
        """
        raise NotImplementedError(p)

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
        return p[1]

    @pg.production("mlhs_head : mlhs_item LITERAL_COMMA")
    def mlhs_head_item(self, p):
        return self.new_list(p[0])

    @pg.production("mlhs_head : mlhs_head mlhs_item LITERAL_COMMA")
    def mlhs_head_head_item(self, p):
        return self.append_to_list(p[0], p[1])

    @pg.production("mlhs_post : mlhs_item")
    def mlhs_post_item(self, p):
        return self.new_list(p[0])

    @pg.production("mlhs_post : mlhs_post LITERAL_COMMA mlhs_item")
    def mlhs_post_post_item(self, p):
        return self.append_to_list(p[0], p[2])

    @pg.production("mlhs_node : variable")
    def mlhs_node_variable(self, p):
        """
        variable {
                    $$ = support.assignable($1, NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_node : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def mlhs_node_subscript(self, p):
        """
        primary_value '[' opt_call_args rbracket {
                    $$ = support.aryset($1, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("mlhs_node : primary_value DOT IDENTIFIER")
    def mlhs_node_attr(self, p):
        """
        primary_value tDOT tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """
        raise NotImplementedError(p)

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
        """
        primary_value tCOLON2 tCONSTANT {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("dynamic constant assignment");
                    }

                    ISourcePosition position = support.getPosition($1);

                    $$ = new ConstDeclNode(position, null, support.new_colon2(position, $1, (String) $3.getValue()), NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

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

    @pg.production("lhs : variable")
    def lhs_variable(self, p):
        """
        variable {
                      // if (!($$ = assignable($1, 0))) $$ = NEW_BEGIN(0);
                    $$ = support.assignable($1, NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

    @pg.production("lhs : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def lhs_subscript(self, p):
        """
        primary_value '[' opt_call_args rbracket {
                    $$ = support.aryset($1, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("lhs : primary_value DOT IDENTIFIER")
    def lhs_dot_identifier(self, p):
        """
        primary_value tDOT tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("lhs : primary_value COLON2 IDENTIFIER")
    def lhs_colon_identifier(self, p):
        """
        primary_value tCOLON2 tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """
        raise NotImplementedError(p)

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
        """
        primary_value tCOLON2 tCONSTANT {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("dynamic constant assignment");
                    }

                    ISourcePosition position = support.getPosition($1);

                    $$ = new ConstDeclNode(position, null, support.new_colon2(position, $1, (String) $3.getValue()), NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

    @pg.production("lhs : COLON3 CONSTANT")
    def lhs_unbound_colon_constant(self, p):
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

    @pg.production("lhs : backref")
    def lhs_backref(self, p):
        self.backref_assign_error()

    @pg.production("cname : IDENTIFIER")
    def cname_identifier(self, p):
        raise self.error(p[0], "class/module name must be CONSTANT")

    @pg.production("cname : CONSTANT")
    def cname_constant(self, p):
        return p[0]

    @pg.production("cpath : COLON3 cname")
    def cpath_unbound_colon_cname(self, p):
        """
        tCOLON3 cname {
                    $$ = support.new_colon3($1.getPosition(), (String) $2.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("cpath : cname")
    def cpath_cname(self, p):
        """
        cname {
                    $$ = support.new_colon2($1.getPosition(), null, (String) $1.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("cpath : primary_value COLON2 cname")
    def cpath_colon_cname(self, p):
        """
        primary_value tCOLON2 cname {
                    $$ = support.new_colon2(support.getPosition($1), $1, (String) $3.getValue());
                }
        """
        raise NotImplementedError(p)

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
        """
        symbol {
                    $$ = new LiteralNode($1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("fitem : fsym")
    def fitem_fsym(self, p):
        return p[0]

    @pg.production("fitem : dsym")
    def fitem_dsym(self, p):
        return p[0]

    @pg.production("undef_list : fitem")
    def undef_list_fitem(self, p):
        """
        fitem {
                    $$ = support.newUndef($1.getPosition(), $1);
                }
        """
        raise NotImplementedError(p)

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
        """
        lhs '=' arg {
                    $$ = support.node_assign($1, $3);
                    // FIXME: Consider fixing node_assign itself rather than single case
                    $<Node>$.setPosition(support.getPosition($1));
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : lhs LITERAL_EQUAL arg RESCUE_MOD arg")
    def arg_lhs_equal_arg_rescue_mod(self, p):
        """
        lhs '=' arg kRESCUE_MOD arg {
                    ISourcePosition position = $4.getPosition();
                    Node body = $5 == null ? NilImplicitNode.NIL : $5;
                    $$ = support.node_assign($1, new RescueNode(position, $3, new RescueBodyNode(position, null, body, null), null));
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : var_lhs OP_ASGN arg")
    def arg_var_lhs_op_asgn_arg(self, p):
        """
        var_lhs tOP_ASGN arg {
                    support.checkExpression($3);

                    ISourcePosition pos = $1.getPosition();
                    String asgnOp = (String) $2.getValue();
                    if (asgnOp.equals("||")) {
                        $1.setValueNode($3);
                        $$ = new OpAsgnOrNode(pos, support.gettable2($1), $1);
                    } else if (asgnOp.equals("&&")) {
                        $1.setValueNode($3);
                        $$ = new OpAsgnAndNode(pos, support.gettable2($1), $1);
                    } else {
                        $1.setValueNode(support.getOperatorCallNode(support.gettable2($1), asgnOp, $3));
                        $1.setPosition(pos);
                        $$ = $1;
                    }
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : var_lhs OP_ASGN arg RESCUE_MOD arg")
    def arg_var_lhs_op_asgn_arg_rescue_mod(self, p):
        """
        var_lhs tOP_ASGN arg kRESCUE_MOD arg {
                    support.checkExpression($3);
                    ISourcePosition pos = $4.getPosition();
                    Node body = $5 == null ? NilImplicitNode.NIL : $5;
                    Node rest;

                    pos = $1.getPosition();
                    String asgnOp = (String) $2.getValue();
                    if (asgnOp.equals("||")) {
                        $1.setValueNode($3);
                        rest = new OpAsgnOrNode(pos, support.gettable2($1), $1);
                    } else if (asgnOp.equals("&&")) {
                        $1.setValueNode($3);
                        rest = new OpAsgnAndNode(pos, support.gettable2($1), $1);
                    } else {
                        $1.setValueNode(support.getOperatorCallNode(support.gettable2($1), asgnOp, $3));
                        $1.setPosition(pos);
                        rest = $1;
                    }

                    $$ = new RescueNode($4.getPosition(), rest, new RescueBodyNode($4.getPosition(), null, body, null), null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : primary_value LITERAL_LBRACKET opt_call_args rbracket OP_ASGN arg")
    def arg_subscript_op_asgn_arg(self, p):
        """
        primary_value '[' opt_call_args rbracket tOP_ASGN arg {
  // FIXME: arg_concat missing for opt_call_args
                    $$ = support.new_opElementAsgnNode(support.getPosition($1), $1, (String) $5.getValue(), $3, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : primary_value DOT IDENTIFIER OP_ASGN arg")
    def arg_method_op_asgn_arg(self, p):
        """
        primary_value tDOT tIDENTIFIER tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """
        raise NotImplementedError(p)

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
        raise self.error(p[2], "constant re-assignment")

    @pg.production("arg : COLON3 CONSTANT OP_ASGN arg")
    def arg_unbound_constant_op_asgn_arg(self, p):
        raise self.error(p[2], "constant re-assignment")

    @pg.production("arg : backref OP_ASGN arg")
    def arg_backref_op_asgn_arg(self, p):
        self.backref_assign_error()

    @pg.production("arg : arg DOT2 arg")
    def arg_dot2(self, p):
        """
        arg tDOT2 arg {
                    support.checkExpression($1);
                    support.checkExpression($3);

                    boolean isLiteral = $1 instanceof FixnumNode && $3 instanceof FixnumNode;
                    $$ = new DotNode(support.getPosition($1), $1, $3, false, isLiteral);
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : arg DOT3 arg")
    def arg_dot3(self, p):
        """
        arg tDOT3 arg {
                    support.checkExpression($1);
                    support.checkExpression($3);

                    boolean isLiteral = $1 instanceof FixnumNode && $3 instanceof FixnumNode;
                    $$ = new DotNode(support.getPosition($1), $1, $3, true, isLiteral);
                }
        """
        raise NotImplementedError(p)

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
        """
        tUMINUS_NUM tINTEGER tPOW arg {
                    $$ = support.getOperatorCallNode(support.getOperatorCallNode($2, "**", $4, lexer.getPosition()), "-@");
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : UMINUS_NUM FLOAT POW arg")
    def arg_uminus_num_float_pow_arg(self, p):
        """
        tUMINUS_NUM tFLOAT tPOW arg {
                    $$ = support.getOperatorCallNode(support.getOperatorCallNode($2, "**", $4, lexer.getPosition()), "-@");
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : UMINUS arg")
    @pg.production("arg : UPLUS arg")
    def arg_uplus_arg(self, p):
        return self.new_unary_call(p[0], p[1])

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
        """
        tBANG arg {
                    $$ = support.getOperatorCallNode(support.getConditionNode($2), "!");
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : TILDE arg")
    def arg_tilde_arg(self, p):
        return self.new_unary_call(p[0], p[1])

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
        """
        kDEFINED opt_nl arg {
                    // ENEBO: arg surrounded by in_defined set/unset
                    $$ = new DefinedNode($1.getPosition(), $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("arg : arg LITERAL_QUESTION_MARK arg opt_nl LITERAL_COLON arg")
    def arg_ternary(self, p):
        """
        arg '?' arg opt_nl ':' arg {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($1), $3, $6);
                }
        """
        raise NotImplementedError(p)

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
        """
        args ',' assocs trailer {
                    $$ = support.arg_append($1, new Hash19Node(lexer.getPosition(), $3));
                }
        """
        raise NotImplementedError(p)

    @pg.production("aref_args : assocs trailer")
    def aref_args_assocs_trailer(self, p):
        """
        assocs trailer {
                    $$ = support.newArrayNode($1.getPosition(), new Hash19Node(lexer.getPosition(), $1));
                }
        """
        raise NotImplementedError(p)

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

    @pg.production("call_args : command")
    def call_args_command(self, p):
        """
        command {
                    $$ = support.newArrayNode(support.getPosition($1), $1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("call_args : args opt_block_arg")
    def call_args_args_opt_block_arg(self, p):
        return self.arg_block_pass(p[0], p[1])

    @pg.production("call_args : assocs opt_block_arg")
    def call_args_assocs_opt_block_arg(self, p):
        """
        assocs opt_block_arg {
                    $$ = support.newArrayNode($1.getPosition(), new Hash19Node(lexer.getPosition(), $1));
                    $$ = support.arg_blk_pass((Node)$$, $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("call_args : args LITERAL_COMMA assocs opt_block_arg")
    def call_args_args_comma_assocs_opt_block_arg(self, p):
        box = self.append_arg(p[0], p[2])
        return self.arg_block_pass(box, p[3])

    @pg.production("call_args : block_arg")
    def call_args_block_arg(self, p):
        """
        block_arg {
                }
        """
        raise NotImplementedError(p)

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

    @pg.production("opt_block_arg : LITERAL_COMMA")
    def opt_block_arg_comma(self, p):
        return None

    @pg.production("opt_block_arg : none_block_pass")
    def opt_block_arg_none(self, p):
        return p[0]

    @pg.production("args : arg_value")
    def args_arg_value(self, p):
        return self.new_args(p[0])

    @pg.production("args : STAR arg_value")
    def args_star_arg_value(self, p):
        return self.new_args(self.new_splat(p[1]))

    @pg.production("args : args LITERAL_COMMA arg_value")
    def args_comma_arg_value(self, p):
        return self.append_arg(p[0], p[2])

    @pg.production("args : args LITERAL_COMMA STAR arg_value")
    def args_comma_star_arg_value(self, p):
        return self.append_arg(p[0], self.new_splat(p[3]))

    @pg.production("mrhs : args LITERAL_COMMA arg_value")
    def mrhs_args_comma_arg_value(self, p):
        """
        args ',' arg_value {
                    Node node = support.splat_array($1);

                    if (node != null) {
                        $$ = support.list_append(node, $3);
                    } else {
                        $$ = support.arg_append($1, $3);
                    }
                }
        """
        raise NotImplementedError(p)

    @pg.production("mrhs : args LITERAL_COMMA STAR arg_value")
    def mrhs_args_comma_star_arg_value(self, p):
        """
        args ',' tSTAR arg_value {
                    Node node = null;

                    if ($4 instanceof ArrayNode &&
                        (node = support.splat_array($1)) != null) {
                        $$ = support.list_concat(node, $4);
                    } else {
                        $$ = support.arg_concat($1.getPosition(), $1, $4);
                    }
                }
        """
        raise NotImplementedError(p)

    @pg.production("mrhs : STAR arg_value")
    def mrhs_star_arg_value(self, p):
        """
        tSTAR arg_value {
                     $$ = support.newSplatNode(support.getPosition($1), $2);
                }
        """
        raise NotImplementedError(p)

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
        """
        tFID {
                    $$ = new FCallNoArgNode($1.getPosition(), (String) $1.getValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : BEGIN bodystmt END")
    def primary_begin_end(self, p):
        """
        kBEGIN bodystmt kEND {
                    $$ = new BeginNode(support.getPosition($1), $2 == null ? NilImplicitNode.NIL : $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : LPAREN_ARG expr paren_post_expr rparen")
    def primary_paren_arg(self, p):
        return p[1]

    @pg.production("paren_post_expr : ")
    def paren_post_expr(self, p):
        self.lexer.state = self.lexer.EXPR_ENDARG

    @pg.production("primary : LPAREN compstmt RPAREN")
    def primary_lparen(self, p):
        """
        tLPAREN compstmt tRPAREN {
                    if ($2 != null) {
                        // compstmt position includes both parens around it
                        ((ISourcePositionHolder) $2).setPosition($1.getPosition());
                        $$ = $2;
                    } else {
                        $$ = new NilNode($1.getPosition());
                    }
                }
        """
        # TODO: null?
        return BoxAST(ast.Block(p[1].getastlist()))

    @pg.production("primary : primary_value COLON2 CONSTANT")
    def primary_constant_lookup(self, p):
        return self.new_colon2(p[0], p[2])

    @pg.production("primary : COLON3 CONSTANT")
    def primary_unbound_constant(self, p):
        return self.new_colon3(p[1])

    @pg.production("primary : LBRACK aref_args RBRACK")
    def primary_array(self, p):
        """
        tLBRACK aref_args tRBRACK {
                    ISourcePosition position = $1.getPosition();
                    if ($2 == null) {
                        $$ = new ZArrayNode(position); /* zero length array */
                    } else {
                        $$ = $2;
                        $<ISourcePositionHolder>$.setPosition(position);
                    }
                }
        """
        if p[1] is None:
            items = []
        else:
            items = p[1].getastlist()
        return BoxAST(ast.Array(items))

    @pg.production("primary : LBRACE assoc_list RCURLY")
    def primary_hash(self, p):
        """
        tLBRACE assoc_list tRCURLY {
                    $$ = new Hash19Node($1.getPosition(), $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : RETURN")
    def primary_return(self, p):
        """
        kRETURN {
                    $$ = new ReturnNode($1.getPosition(), NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : YIELD LPAREN2 call_args rparen")
    def primary_yield_paren_args(self, p):
        """
        kYIELD tLPAREN2 call_args rparen {
                    $$ = support.new_yield($1.getPosition(), $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : YIELD LPAREN2 rparen")
    def primary_yield_paren(self, p):
        """
        kYIELD tLPAREN2 rparen {
                    $$ = new ZYieldNode($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : YIELD")
    def primary_yield(self, p):
        """
        kYIELD {
                    $$ = new ZYieldNode($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : DEFINED opt_nl LPAREN2 expr rparen")
    def primary_defined(self, p):
        """
        kDEFINED opt_nl tLPAREN2 expr rparen {
                    $$ = new DefinedNode($1.getPosition(), $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : NOT LPAREN2 expr rparen")
    def primary_not_paren_expr(self, p):
        """
        kNOT tLPAREN2 expr rparen {
                    $$ = support.getOperatorCallNode(support.getConditionNode($3), "!");
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : NOT LPAREN2 rparen")
    def primary_not_paren(self, p):
        """
        kNOT tLPAREN2 rparen {
                    $$ = support.getOperatorCallNode(NilImplicitNode.NIL, "!");
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : operation brace_block")
    def primary_operation_brace_block(self, p):
        """
        operation brace_block {
                    $$ = new FCallNoArgBlockNode($1.getPosition(), (String) $1.getValue(), $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : method_call")
    def primary_method_call(self, p):
        return p[0]

    @pg.production("primary : method_call brace_block")
    def primary_method_call_brace_block(self, p):
        """
        method_call brace_block {
                    if ($1 != null &&
                          $<BlockAcceptingNode>1.getIterNode() instanceof BlockPassNode) {
                        throw new SyntaxException(PID.BLOCK_ARG_AND_BLOCK_GIVEN, $1.getPosition(), lexer.getCurrentLine(), "Both block arg and actual block given.");
                    }
                    $$ = $<BlockAcceptingNode>1.setIterNode($2);
                    $<Node>$.setPosition($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : LAMBDA lambda")
    def primary_lambda(self, p):
        return p[0]

    @pg.production("primary : IF expr_value then compstmt if_tail END")
    def primary_if(self, p):
        return BoxAST(ast.If(
            p[1].getast(),
            ast.Block(p[3].getastlist()) if p[3] else ast.Nil(),
            p[4].getast() if p[4] else ast.Nil()
        ))

    @pg.production("primary : UNLESS expr_value then compstmt opt_else END")
    def primary_unless(self, p):
        """
        kUNLESS expr_value then compstmt opt_else kEND {
                    $$ = new IfNode($1.getPosition(), support.getConditionNode($2), $5, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : WHILE expr_value do compstmt END")
    def primary_while(self, p):
        """
        kWHILE {
                    lexer.getConditionState().begin();
                } expr_value do {
                    lexer.getConditionState().end();
                } compstmt kEND {
                    Node body = $6 == null ? NilImplicitNode.NIL : $6;
                    $$ = new WhileNode($1.getPosition(), support.getConditionNode($3), body);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : UNTIL expr_value do compstmt END")
    def primary_until(self, p):
        """
        kUNTIL {
                  lexer.getConditionState().begin();
                } expr_value do {
                  lexer.getConditionState().end();
                } compstmt kEND {
                    Node body = $6 == null ? NilImplicitNode.NIL : $6;
                    $$ = new UntilNode($1.getPosition(), support.getConditionNode($3), body);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : CASE expr_value opt_terms case_body END")
    def primary_case_expr_value(self, p):
        """
        kCASE expr_value opt_terms case_body kEND {
                    $$ = support.newCaseNode($1.getPosition(), $2, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : CASE opt_terms case_body END")
    def primary_case(self, p):
        """
        kCASE opt_terms case_body kEND {
                    $$ = support.newCaseNode($1.getPosition(), null, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : FOR for_var IN expr_value do compstmt END")
    def primary_for(self, p):
        """
        kFOR for_var kIN {
                    lexer.getConditionState().begin();
                } expr_value do {
                    lexer.getConditionState().end();
                } compstmt kEND {
                      // ENEBO: Lots of optz in 1.9 parser here
                    $$ = new ForNode($1.getPosition(), $2, $8, $5, support.getCurrentScope());
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : CLASS cpath superclass bodystmt END")
    def primary_class(self, p):
        """
        kCLASS cpath superclass {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("class definition in method body");
                    }
                    support.pushLocalScope();
                } bodystmt kEND {
                    Node body = $5 == null ? NilImplicitNode.NIL : $5;

                    $$ = new ClassNode($1.getPosition(), $<Colon3Node>2, support.getCurrentScope(), body, $3);
                    support.popCurrentScope();
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : CLASS LSHFT expr term bodystmt END")
    def primary_singleton_class(self, p):
        """
        kCLASS tLSHFT expr {
                    $$ = Boolean.valueOf(support.isInDef());
                    support.setInDef(false);
                } term {
                    $$ = Integer.valueOf(support.getInSingle());
                    support.setInSingle(0);
                    support.pushLocalScope();
                } bodystmt kEND {
                    $$ = new SClassNode($1.getPosition(), $3, support.getCurrentScope(), $7);
                    support.popCurrentScope();
                    support.setInDef($<Boolean>4.booleanValue());
                    support.setInSingle($<Integer>6.intValue());
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : MODULE cpath bodystmt END")
    def primary_module(self, p):
        """
        kMODULE cpath {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("module definition in method body");
                    }
                    support.pushLocalScope();
                } bodystmt kEND {
                    Node body = $4 == null ? NilImplicitNode.NIL : $4;

                    $$ = new ModuleNode($1.getPosition(), $<Colon3Node>2, support.getCurrentScope(), body);
                    support.popCurrentScope();
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : DEF fname f_arglist bodystmt END")
    def primary_def(self, p):
        """
        kDEF fname {
                    support.setInDef(true);
                    support.pushLocalScope();
                } f_arglist bodystmt kEND {
                    // TODO: We should use implicit nil for body, but problem (punt til later)
                    Node body = $5; //$5 == null ? NilImplicitNode.NIL : $5;

                    $$ = new DefnNode($1.getPosition(), new ArgumentNode($2.getPosition(), (String) $2.getValue()), $4, support.getCurrentScope(), body);
                    support.popCurrentScope();
                    support.setInDef(false);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : DEF singleton dot_or_colon fname f_arglist bodystmt END")
    def primary_def_singleton(self, p):
        """
        kDEF singleton dot_or_colon {
                    lexer.setState(LexState.EXPR_FNAME);
                } fname {
                    support.setInSingle(support.getInSingle() + 1);
                    support.pushLocalScope();
                    lexer.setState(LexState.EXPR_ENDFN); /* force for args */
                } f_arglist bodystmt kEND {
                    // TODO: We should use implicit nil for body, but problem (punt til later)
                    Node body = $8; //$8 == null ? NilImplicitNode.NIL : $8;

                    $$ = new DefsNode($1.getPosition(), $2, new ArgumentNode($5.getPosition(), (String) $5.getValue()), $7, support.getCurrentScope(), body);
                    support.popCurrentScope();
                    support.setInSingle(support.getInSingle() - 1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : BREAK")
    def primary_break(self, p):
        """
        kBREAK {
                    $$ = new BreakNode($1.getPosition(), NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

    @pg.production("primary : NEXT")
    def primary_next(self, p):
        """
        kNEXT {
                    $$ = new NextNode($1.getPosition(), NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

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
        return BoxAST(ast.Block(p[1].getastlist()))

    @pg.production("for_var : mlhs")
    @pg.production("for_var : lhs")
    def for_var(self, p):
        return p[0]

    @pg.production("f_marg : f_norm_arg")
    def f_marg_f_norm_arg(self, p):
        """
        f_norm_arg {
                     $$ = support.assignable($1, NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_marg : LPAREN f_margs rparen")
    def f_marg_paren(self, p):
        return p[1]

    @pg.production("f_marg_list : f_marg")
    def f_marg_list_f_marg(self, p):
        """
        f_marg {
                    $$ = support.newArrayNode($1.getPosition(), $1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_marg_list : f_marg_list LITERAL_COMMA f_marg")
    def f_marg_list(self, p):
        """
        f_marg_list ',' f_marg {
                    $$ = $1.add($3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : f_marg_list")
    def f_margs_f_marg_list(self, p):
        """
        f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, null, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR f_norm_arg")
    def f_margs_f_marg_list_comma_star_f_norm_Arg(self, p):
        """
        f_marg_list ',' tSTAR f_norm_arg {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, support.assignable($4, null), null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR f_norm_arg LITERAL_COMMA f_marg_list")
    def f_margs_f_marg_list_comma_star_f_norm_arg_comm_f_marg_list(self, p):
        """
        f_marg_list ',' tSTAR f_norm_arg ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, support.assignable($4, null), $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR")
    def f_margs_f_marg_list_comma_star(self, p):
        """
        f_marg_list ',' tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR LITERAL_COMMA f_marg_list")
    def f_margs_f_marg_list_comma_star_comma_f_marg_list(self, p):
        """
        f_marg_list ',' tSTAR ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), $5);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : STAR f_norm_arg")
    def f_margs_star_f_norm_arg(self, p):
        """
        tSTAR f_norm_arg {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, support.assignable($2, null), null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : STAR f_norm_arg LITERAL_COMMA f_marg_list")
    def f_margs_star_f_norm_arg_comma_f_marg_list(self, p):
        """
        tSTAR f_norm_arg ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, support.assignable($2, null), $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : STAR")
    def f_margs_star(self, p):
        """
        tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_margs : STAR LITERAL_COMMA f_marg_list")
    def f_margs_star_comma_f_marg_list(self, p):
        """
        tSTAR ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, null, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_block_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, null, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_block_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, $7, $8);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_block_optarg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, null, $4);
                }
        """
        raise NotImplementedError(p)

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
        """
        f_arg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, null, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_arg LITERAL_COMMA")
    def block_param_f_arg_comma(self, p):
        """
        f_arg ',' {
                    RestArgNode rest = new UnnamedRestArgNode($1.getPosition(), null, support.getCurrentScope().addVariable("*"));
                    $$ = support.new_args($1.getPosition(), $1, null, rest, null, null);
                }
        """
        raise NotImplementedError(p)

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
        """
        f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, null, null, $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_param : f_block_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def block_param_f_block_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_block_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, $3, null, $4);
                }
        """
        raise NotImplementedError(p)

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
        """
        f_block_optarg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, null, null, $2);
                }
        """
        raise NotImplementedError(p)

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
        """
        f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, $1, null, $2);
                }
        """
        raise NotImplementedError(p)

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
        """
        f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, $1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("opt_block_param : none")
    def opt_block_param_none(self, p):
        """
        none {
    // was $$ = null;
                   $$ = support.new_args(lexer.getPosition(), null, null, null, null, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("opt_block_param : block_param_def")
    def opt_block_param(self, p):
        """
        block_param_def {
                    lexer.commandStart = true;
                    $$ = $1;
                }
        """
        raise NotImplementedError(p)

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
        """
        tOROP {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, null);
                }
        """
        raise NotImplementedError(p)

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

    @pg.production("lambda : f_larglist lambda_body")
    def lambda_p(self, p):
        """
        /* none */  {
                    support.pushBlockScope();
                    $$ = lexer.getLeftParenBegin();
                    lexer.setLeftParenBegin(lexer.incrementParenNest());
                } f_larglist lambda_body {
                    $$ = new LambdaNode($2.getPosition(), $2, $3, support.getCurrentScope());
                    support.popCurrentScope();
                    lexer.setLeftParenBegin($<Integer>1);
                }
        """
        raise NotImplementedError(p)

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

    @pg.production("do_block : DO_BLOCK opt_block_param compstmt END")
    def do_block(self, p):
        """
        kDO_BLOCK {
                    support.pushBlockScope();
                } opt_block_param compstmt kEND {
                    $$ = new IterNode(support.getPosition($1), $3, $4, support.getCurrentScope());
                    support.popCurrentScope();
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_call : command do_block")
    def block_call_command_do_block(self, p):
        """
        command do_block {
                    // Workaround for JRUBY-2326 (MRI does not enter this production for some reason)
                    if ($1 instanceof YieldNode) {
                        throw new SyntaxException(PID.BLOCK_GIVEN_TO_YIELD, $1.getPosition(), lexer.getCurrentLine(), "block given to yield");
                    }
                    if ($<BlockAcceptingNode>1.getIterNode() instanceof BlockPassNode) {
                        throw new SyntaxException(PID.BLOCK_ARG_AND_BLOCK_GIVEN, $1.getPosition(), lexer.getCurrentLine(), "Both block arg and actual block given.");
                    }
                    $$ = $<BlockAcceptingNode>1.setIterNode($2);
                    $<Node>$.setPosition($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("block_arg : block_call DOT operation2 opt_paren_args")
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
        """
        primary_value tCOLON2 operation2 paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("method_call : primary_value COLON2 operation3")
    def method_call_primary_value_colon_operation(self, p):
        """
        primary_value tCOLON2 operation3 {
                    $$ = support.new_call($1, $3, null, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("method_call : primary_value DOT paren_args")
    def method_call_primary_value_dot_paren_args(self, p):
        """
        primary_value tDOT paren_args {
                    $$ = support.new_call($1, new Token("call", $1.getPosition()), $3, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("method_call : primary_value COLON2 paren_args")
    def method_call_primary_value_colon_paren_args(self, p):
        """
        primary_value tCOLON2 paren_args {
                    $$ = support.new_call($1, new Token("call", $1.getPosition()), $3, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("method_call : SUPER paren_args")
    def method_call_super_paren_args(self, p):
        """
        kSUPER paren_args {
                    $$ = support.new_super($2, $1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("method_call : SUPER")
    def method_call_super(self, p):
        """
        kSUPER {
                    $$ = new ZSuperNode($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("method_call : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def method_call_primary_value_lbracket_opt_call_args_rbracket(self, p):
        return self.new_call(p[0], self.new_token(p[1], "[]"), p[2])

    @pg.production("brace_block : LCURLY opt_block_param compstmt RCURLY")
    def brace_block_curly(self, p):
        """
        tLCURLY {
                    support.pushBlockScope();
                } opt_block_param compstmt tRCURLY {
                    $$ = new IterNode($1.getPosition(), $3, $4, support.getCurrentScope());
                    support.popCurrentScope();
                }
        """
        raise NotImplementedError(p)

    @pg.production("brace_block : DO opt_block_param compstmt END")
    def brace_block_do(self, p):
        """
        kDO {
                    support.pushBlockScope();
                } opt_block_param compstmt kEND {
                    $$ = new IterNode($1.getPosition(), $3, $4, support.getCurrentScope());
                    // FIXME: What the hell is this?
                    $<ISourcePositionHolder>0.setPosition(support.getPosition($<ISourcePositionHolder>0));
                    support.popCurrentScope();
                }
        """
        raise NotImplementedError(p)

    @pg.production("case_body : WHEN args then compstmt cases")
    def case_body(self, p):
        """
        kWHEN args then compstmt cases {
                    $$ = support.newWhenNode($1.getPosition(), $2, $4, $5);
                }
        """
        raise NotImplementedError(p)

    @pg.production("cases : opt_else")
    def cases_opt_else(self, p):
        return p[0]

    @pg.production("cases : case_body")
    def cases_case_body(self, p):
        return p[0]

    @pg.production("opt_rescue : RESCUE exc_list exc_var then compstmt opt_rescue")
    def opt_rescue(self, p):
        """"
        kRESCUE exc_list exc_var then compstmt opt_rescue {
                    Node node;
                    if ($3 != null) {
                        node = support.appendToBlock(support.node_assign($3, new GlobalVarNode($1.getPosition(), "$!")), $5);
                        if ($5 != null) {
                            node.setPosition(support.unwrapNewlineNode($5).getPosition());
                        }
                    } else {
                        node = $5;
                    }
                    Node body = node == null ? NilImplicitNode.NIL : node;
                    $$ = new RescueBodyNode($1.getPosition(), $2, body, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("opt_rescue : ")
    def opt_rescue_empty(self, p):
        return None

    @pg.production("exc_list : arg_value")
    def exc_list_arg_value(self, p):
        """
        arg_value {
                    $$ = support.newArrayNode($1.getPosition(), $1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("exc_list : mrhs")
    def exc_list_mrhs(self, p):
        """
        mrhs {
                    $$ = support.splat_array($1);
                    if ($$ == null) $$ = $1;
                }
        """
        raise NotImplementedError(p)

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
        """
        string {
                    $$ = $1 instanceof EvStrNode ? new DStrNode($1.getPosition(), lexer.getEncoding()).add($1) : $1;
                }
        """
        # TODO: understand this logic
        return p[0]

    @pg.production("string : CHAR")
    def string_char(self, p):
        """
        tCHAR {
                    ByteList aChar = ByteList.create((String) $1.getValue());
                    aChar.setEncoding(lexer.getEncoding());
                    $$ = lexer.createStrNode($<Token>0.getPosition(), aChar, 0);
                }
        """
        # TODO: encoding
        return BoxAST(ast.ConstantString(p[0].getstr()))

    @pg.production("string : string1")
    def string_string1(self, p):
        return p[0]

    @pg.production("string : string string1")
    def string_string_string1(self, p):
        """
        string string1 {
                    $$ = support.literal_concat($1.getPosition(), $1, $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("string1 : STRING_BEG string_contents STRING_END")
    def string1(self, p):
        """
        tSTRING_BEG string_contents tSTRING_END {
                    $$ = $2;

                    $<ISourcePositionHolder>$.setPosition($1.getPosition());
                    int extraLength = ((String) $1.getValue()).length() - 1;

                    // We may need to subtract addition offset off of first
                    // string fragment (we optimistically take one off in
                    // ParserSupport.literal_concat).  Check token length
                    // and subtract as neeeded.
                    if (($2 instanceof DStrNode) && extraLength > 0) {
                      Node strNode = ((DStrNode)$2).get(0);
                    }
                }
        """
        raise NotImplementedError(p)

    @pg.production("xstring : XSTRING_BEG xstring_contents STRING_END")
    def xstring(self, p):
        """
        tXSTRING_BEG xstring_contents tSTRING_END {
                    ISourcePosition position = $1.getPosition();

                    if ($2 == null) {
                        $$ = new XStrNode(position, null);
                    } else if ($2 instanceof StrNode) {
                        $$ = new XStrNode(position, (ByteList) $<StrNode>2.getValue().clone());
                    } else if ($2 instanceof DStrNode) {
                        $$ = new DXStrNode(position, $<DStrNode>2);

                        $<Node>$.setPosition(position);
                    } else {
                        $$ = new DXStrNode(position).add($2);
                    }
                }
        """
        raise NotImplementedError(p)

    @pg.production("regexp : REGEXP_BEG xstring_contents REGEXP_END")
    def regexp(self, p):
        """
        tREGEXP_BEG xstring_contents tREGEXP_END {
                    $$ = support.newRegexpNode($1.getPosition(), $2, (RegexpNode) $3);
                }
        """
        n = p[1].getast()
        if isinstance(n, ast.ConstantString):
            node = ast.ConstantRegexp(n.strvalue)
        else:
            node = ast.DynamicRegexp(n)
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
        return p[1]

    @pg.production("word_list : ")
    def word_list_empty(self, p):
        """
        /* none */ {
                    $$ = new ArrayNode(lexer.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("word_list : word_list word LITERAL_SPACE")
    def word_list(self, p):
        """
        word_list word ' ' {
                     $$ = $1.add($2 instanceof EvStrNode ? new DStrNode($1.getPosition(), lexer.getEncoding()).add($2) : $2);
                }
        """
        raise NotImplementedError(p)

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
        """
        tQWORDS_BEG ' ' tSTRING_END {
                     $$ = new ZArrayNode($1.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("qwords : QWORDS_BEG qword_list STRING_END")
    def qwords_qword_list(self, p):
        return p[1]

    @pg.production("qword_list : ")
    def qword_list_empty(self, p):
        """
        /* none */ {
                    $$ = new ArrayNode(lexer.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("qword_list : qword_list STRING_CONTENT LITERAL_SPACE")
    def qword_list(self, p):
        """
        qword_list tSTRING_CONTENT ' ' {
                    $$ = $1.add($2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("string_contents : ")
    def string_contents_empty(self, p):
        """
        /* none */ {
                    ByteList aChar = ByteList.create("");
                    aChar.setEncoding(lexer.getEncoding());
                    $$ = lexer.createStrNode($<Token>0.getPosition(), aChar, 0);
                }
        """
        raise NotImplementedError(p)

    @pg.production("string_contents : string_contents string_content")
    def string_contents(self, p):
        """
        string_contents string_content {
                    $$ = support.literal_concat($1.getPosition(), $1, $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("xstring_contents : ")
    def xstring_contents_empty(self, p):
        return None

    @pg.production("xstring_contents : xstring_contents string_content")
    def xstring_contents(self, p):
        return self.concat_literals(p[0], p[1])

    @pg.production("string_content : STRING_CONTENT")
    def string_content_string_content(self, p):
        return BoxAST(ast.ConstantString(p[0].getstr()))

    @pg.production("string_content : STRING_DVAR string_dvar")
    def string_content_string_dvar(self, p):
        """
        tSTRING_DVAR {
                    $$ = lexer.getStrTerm();
                    lexer.setStrTerm(null);
                    lexer.setState(LexState.EXPR_BEG);
                } string_dvar {
                    lexer.setStrTerm($<StrTerm>2);
                    $$ = new EvStrNode($1.getPosition(), $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("string_content : STRING_DBEG compstmt RCURLY")
    def string_content_string_dbeg(self, p):
        """
        tSTRING_DBEG {
                   $$ = lexer.getStrTerm();
                   lexer.getConditionState().stop();
                   lexer.getCmdArgumentState().stop();
                   lexer.setStrTerm(null);
                   lexer.setState(LexState.EXPR_BEG);
                } compstmt tRCURLY {
                   lexer.getConditionState().restart();
                   lexer.getCmdArgumentState().restart();
                   lexer.setStrTerm($<StrTerm>2);

                   $$ = support.newEvStrNode($1.getPosition(), $3);
                }
        """
        raise NotImplementedError(p)

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
        """"
        tSYMBEG xstring_contents tSTRING_END {
                     lexer.setState(LexState.EXPR_END);

                     // DStrNode: :"some text #{some expression}"
                     // StrNode: :"some text"
                     // EvStrNode :"#{some expression}"
                     // Ruby 1.9 allows empty strings as symbols
                     if ($2 == null) {
                         $$ = new SymbolNode($1.getPosition(), "");
                     } else if ($2 instanceof DStrNode) {
                         $$ = new DSymbolNode($1.getPosition(), $<DStrNode>2);
                     } else if ($2 instanceof StrNode) {
                         $$ = new SymbolNode($1.getPosition(), $<StrNode>2.getValue().toString().intern());
                     } else {
                         $$ = new DSymbolNode($1.getPosition());
                         $<DSymbolNode>$.add($2);
                     }
                }
        """
        raise NotImplementedError(p)

    @pg.production("numeric : INTEGER")
    def numeric_integer(self, p):
        s = p[0].getstr()
        if "X" in s:
            base = 16
        elif "O" in s:
            base = 8
        elif "B" in s:
            base = 2
        else:
            base = 10
        return BoxAST(ast.ConstantInt(int(s, base)))

    @pg.production("numeric : FLOAT")
    def numeric_float(self, p):
        return BoxAST(ast.ConstantFloat(float(p[0].getstr())))

    @pg.production("numeric : UMINUS_NUM INTEGER", precedence="LOWEST")
    def numeric_minus_integer(self, p):
        raise NotImplementedError

    @pg.production("numeric : UMINUS_NUM FLOAT", precedence="LOWEST")
    def numeric_minus_float(self, p):
        raise NotImplementedError

    @pg.production("variable : IDENTIFIER")
    def variable_identifier(self, p):
        return BoxAST(ast.Variable(p[0].getstr(), p[0].getsourcepos().lineno))

    @pg.production("variable : IVAR")
    def variable_ivar(self, p):
        return BoxAST(ast.InstanceVariable(p[0].getstr()))

    @pg.production("variable : GVAR")
    def variable_gvar(self, p):
        return BoxAST(ast.Global(p[0].getstr()))

    @pg.production("variable : CONSTANT")
    def variable_constant(self, p):
        return BoxAST(ast.LookupConstant(
            ast.Scope(p[0].getsourcepos().lineno),
            p[0].getstr(),
            p[0].getsourcepos().lineno
        ))

    @pg.production("variable : CVAR")
    def variable_cvar(self, p):
        raise NotImplementedError

    @pg.production("variable : NIL")
    def variable_nil(self, p):
        return BoxAST(ast.Nil())

    @pg.production("variable : SELF")
    def variable_self(self, p):
        return BoxAST(ast.Self())

    @pg.production("variable : TRUE")
    def variable_true(self, p):
        return BoxAST(ast.ConstantBoolean(True))

    @pg.production("variable : FALSE")
    def variable_false(self, p):
        return BoxAST(ast.ConstantBoolean(False))

    @pg.production("variable : __FILE__")
    def variable__file__(self, p):
        return BoxAST(ast.File())

    @pg.production("variable : __LINE__")
    def variable__line__(self, p):
        return BoxAST(ast.ConstantInt(p[0].getsourcepos().lineno))

    @pg.production("variable : __ENCODING__")
    def variable__encoding__(self, p):
        return BoxAST(ast.Encoding())

    @pg.production("var_ref : variable")
    def var_ref(self, p):
        """
        variable {
                    $$ = support.gettable($1);
                }
        """
        # TODO: symtable support?
        return p[0]

    @pg.production("var_lhs : variable")
    def var_lhs(self, p):
        """
        variable {
                    $$ = support.assignable($1, NilImplicitNode.NIL);
                }
        """
        raise NotImplementedError(p)

    @pg.production("backref : BACK_REF")
    @pg.production("backref : NTH_REF")
    def backref(self, p):
        return p[0]

    @pg.production("superclass : term")
    def superclass_term(self, p):
        return None

    @pg.production("superclass : LT expr_value term")
    def superclass(self, p):
        """"
        tLT {
                   lexer.setState(LexState.EXPR_BEG);
                } expr_value term {
                    $$ = $3;
                }
        """
        raise NotImplementedError(p)

    @pg.production("superclass : error term")
    def superclass_error(self, p):
        return None

    @pg.production("f_arglist : LPAREN2 f_args rparen")
    def f_arglist_parens(self, p):
        self.lexer.state = self.lexer.EXPR_BEG
        return p[1]

    @pg.production("f_arglist : f_args term")
    def f_arglist(self, p):
        return p[0]

    @pg.production("f_args : f_arg LITERAL_COMMA f_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def f_args_f_arg_comma_f_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, null, $6);
                }
        """
        raise NotImplementedError(p)

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
        """
        f_arg ',' f_optarg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, null, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_arg LITERAL_COMMA f_optarg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_arg_comma_f_optarg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, $5, $6);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_arg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def f_args_f_arg_comma_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, null, $4);
                }
        """
        raise NotImplementedError(p)

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
        """
        f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, null, null, $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def f_args_f_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, $3, null, $4);
                }
        """
        raise NotImplementedError(p)

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
        """
        f_optarg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, null, null, $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_optarg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_optarg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, null, $3, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_rest_arg opt_f_block_arg")
    def f_args_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, $1, null, $2);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def f_args_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, $1, $3, $4);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : f_block_arg")
    def f_args_f_block_arg(self, p):
        """
        f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, $1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_args : ")
    def f_args_none(self, p):
        """
        /* none */ {
                    $$ = support.new_args(lexer.getPosition(), null, null, null, null, null);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_bad_arg : CONSTANT")
    def f_bad_arg_constant(self, p):
        raise self.error(p[0], "formal argument cannot be a constant")

    @pg.production("f_bad_arg : IVAR")
    def f_bad_arg_invar(self, p):
        raise self.error(p[0], "formal argument cannot be an instance variable")

    @pg.production("f_bad_arg : GVAR")
    def f_bad_arg_gvar(self, p):
        raise self.error(p[0], "formal argument cannot be a global variable")

    @pg.production("f_bad_arg : CVAR")
    def f_bad_arg_cvar(self, p):
        raise self.error(p[0], "formal argument cannot be a class variable")

    @pg.production("f_norm_arg : f_bad_arg")
    def f_norm_arg_f_bad_arg(self, p):
        return p[0]

    @pg.production("f_norm_arg : IDENTIFIER")
    def f_norm_arg_identifier(self, p):
        """
        tIDENTIFIER {
                    $$ = support.formal_argument($1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_arg_item : f_norm_arg")
    def f_arg_item_f_norm_arg(self, p):
        """
        f_norm_arg {
                    $$ = support.arg_var($1);
  /*
                    $$ = new ArgAuxiliaryNode($1.getPosition(), (String) $1.getValue(), 1);
  */
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_arg_item : LPAREN f_margs rparen")
    def f_arg_item_paren(self, p):
        """
        tLPAREN f_margs rparen {
                    $$ = $2;
                    /*          {
            ID tid = internal_id();
            arg_var(tid);
            if (dyna_in_block()) {
                $2->nd_value = NEW_DVAR(tid);
            }
            else {
                $2->nd_value = NEW_LVAR(tid);
            }
            $$ = NEW_ARGS_AUX(tid, 1);
            $$->nd_next = $2;*/
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_arg : f_arg_item")
    def f_arg_f_arg_item(self, p):
        """
        f_arg_item {
                    $$ = new ArrayNode(lexer.getPosition(), $1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_arg : f_arg LITERAL_COMMA f_arg_item")
    def f_arg(self, p):
        """
        f_arg ',' f_arg_item {
                    $1.add($3);
                    $$ = $1;
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_opt : IDENTIFIER LITERAL_EQUAL arg_value")
    def f_opt(self, p):
        """
        tIDENTIFIER '=' arg_value {
                    support.arg_var(support.formal_argument($1));
                    $$ = new OptArgNode($1.getPosition(), support.assignable($1, $3));
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_block_opt : IDENTIFIER LITERAL_EQUAL primary_value")
    def f_block_opt(self, p):
        """
        tIDENTIFIER '=' primary_value {
                    support.arg_var(support.formal_argument($1));
                    $$ = new OptArgNode($1.getPosition(), support.assignable($1, $3));
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_block_optarg : f_block_opt")
    def f_block_optarg_f_block_opt(self, p):
        """
        f_block_opt {
                    $$ = new BlockNode($1.getPosition()).add($1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_block_optarg : f_block_optarg LITERAL_COMMA f_block_opt")
    def f_block_optarg(self, p):
        """
        f_block_optarg ',' f_block_opt {
                    $$ = support.appendToBlock($1, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_optarg : f_opt")
    def f_optarg_f_opt(self, p):
        """
        f_opt {
                    $$ = new BlockNode($1.getPosition()).add($1);
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_optarg : f_optarg LITERAL_COMMA f_opt")
    def f_optarg(self, p):
        """
        f_optarg ',' f_opt {
                    $$ = support.appendToBlock($1, $3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("restarg_mark : STAR")
    @pg.production("restarg_mark : STAR2")
    def restarg_mark(self, p):
        return p[0]

    @pg.production("f_rest_arg : restarg_mark IDENTIFIER")
    def f_rest_arg_restarg_mark_identifer(self, p):
        """
        restarg_mark tIDENTIFIER {
                    if (!support.is_local_id($2)) {
                        support.yyerror("rest argument must be local variable");
                    }

                    $$ = new RestArgNode(support.arg_var(support.shadowing_lvar($2)));
                }
        """
        raise NotImplementedError(p)

    @pg.production("f_rest_arg : restarg_mark")
    def f_rest_arg_restarg_mark(self, p):
        """
        restarg_mark {
                    $$ = new UnnamedRestArgNode($1.getPosition(), "", support.getCurrentScope().addVariable("*"));
                }
        """
        raise NotImplementedError(p)

    @pg.production("blkarg_mark : AMPER")
    @pg.production("blkarg_mark : AMPER2")
    def blkarg_mark(self, p):
        return p[0]

    @pg.production("f_block_arg : blkarg_mark IDENTIFIER")
    def f_block_arg(self, p):
        """
        blkarg_mark tIDENTIFIER {
                    if (!support.is_local_id($2)) {
                        support.yyerror("block argument must be local variable");
                    }

                    $$ = new BlockArgNode(support.arg_var(support.shadowing_lvar($2)));
                }
        """
        raise NotImplementedError(p)

    @pg.production("opt_f_block_arg : LITERAL_COMMA f_block_arg")
    def opt_f_block_arg(self, p):
        return p[1]

    @pg.production("opt_f_block_arg : ")
    def opt_f_block_arg_empty(self, p):
        return None

    @pg.production("singleton : var_ref")
    def singleton_var_ref(self, p):
        """
        var_ref {
                    if (!($1 instanceof SelfNode)) {
                        support.checkExpression($1);
                    }
                    $$ = $1;
                }
        """
        raise NotImplementedError(p)

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
        """
        none {
                    $$ = new ArrayNode(lexer.getPosition());
                }
        """
        raise NotImplementedError(p)

    @pg.production("assoc_list : assocs trailer")
    def assoc_list(self, p):
        return p[0]

    @pg.production("assocs : assoc")
    def assocs_assoc(self, p):
        [key, value] = p[0].getastlist()
        return BoxAST(ast.Hash([(key, value)]))

    @pg.production("assocs : assocs LITERAL_COMMA assoc")
    def assocs(self, p):
        """
        assocs ',' assoc {
                    $$ = $1.addAll($3);
                }
        """
        raise NotImplementedError(p)

    @pg.production("assoc : arg_value ASSOC arg_value")
    def assoc_arg_value(self, p):
        return self.append_to_list(self.new_list(p[0]), p[2])

    @pg.production("assoc : LABEL arg_value")
    def assoc_label(self, p):
        """
        tLABEL arg_value {
                    ISourcePosition pos = $1.getPosition();
                    $$ = support.newArrayNode(pos, new SymbolNode(pos, (String) $1.getValue())).add($2);
                }
        """
        raise NotImplementedError(p)

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
        BaseBox.__init__(self)
        self.node = node

    def getast(self):
        return self.node


class BoxASTList(BaseBox):
    def __init__(self, nodes):
        BaseBox.__init__(self)
        self.nodes = nodes

    def getastlist(self):
        return self.nodes


class BoxArgs(BaseBox):
    def __init__(self, args, block):
        BaseBox.__init__(self)
        self.args = args
        self.block = block

    def getargs(self):
        return self.args

    def getblock(self):
        return self.block


class BoxInt(BaseBox):
    def __init__(self, intvalue):
        BaseBox.__init__(self)
        self.intvalue = intvalue

    def getint(self):
        return self.intvalue
