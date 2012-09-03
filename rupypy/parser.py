from rply import ParserGenerator


class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer

    def parse(self):
        l = LexerWrapper(self.lexer.tokenize())
        return self.parser.parse(l, state=self)

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
        "LBRACK", "RBRACE", "LBRACE", "LBRACE_ARG", "STAR", "STAR2", "AMPER",
        "AMPER2", "TILDE", "PERCENT", "DIVIDE", "PLUS", "MINUS", "LT", "GT",
        "PIPE", "BANG", "CARET", "LCURLY", "RCURLY", "BACK_REF2", "SYMBEG",
        "STRING_BEG", "XSTRING_BEG", "REGEXP_BEG", "WORDS_BEG", "QWORDS_BEG",
        "STRING_DBEG", "STRING_DVAR", "STRING_END", "LAMBDA", "LAMBEG",
        "NTH_REF", "BACK_REF", "STRING_CONTENT", "INTEGER", "FLOAT",
        "REGEXP_END",
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

    @pg.production("top_compstmt : top_stmts opt_terms")
    def top_compstmt(self, p):
        """
top_compstmt  : top_stmts opt_terms {
                  if ($1 instanceof BlockNode) {
                      support.checkUselessStatements($<BlockNode>1);
                  }
                  $$ = $1;
              }
        """

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

    @pg.production("stmt : ALIAS fitem fitem")
    def stmt_alias_fitem(self, p):
        """
        kALIAS fitem {
                    lexer.setState(LexState.EXPR_FNAME);
                } fitem {
                    $$ = support.newAlias($1.getPosition(), $2, $4);
                }
        """

    @pg.production("stmt : ALIAS GVAR GVAR")
    def stmt_alias_gvar(self, p):
        """
kALIAS tGVAR tGVAR {
                    $$ = new VAliasNode($1.getPosition(), (String) $2.getValue(), (String) $3.getValue());
                }
        """

    @pg.production("stmt : ALIAS GVAR BACK_REF")
    def stmt_alias_gvar_backref(self, p):
        """
        kALIAS tGVAR tBACK_REF {
                    $$ = new VAliasNode($1.getPosition(), (String) $2.getValue(), "$" + $<BackRefNode>3.getType());
                }
        """

    @pg.production("stmt : ALIAS GVAR NTH_REF")
    def stmt_alias_gvar_nref(self, p):
        """
        kALIAS tGVAR tNTH_REF {
                    support.yyerror("can't make alias for the number variables");
                }
        """

    @pg.production("stmt : UNDEF undef_list")
    def stmt_undef(self, p):
        """
        kUNDEF undef_list {
                    $$ = $2;
                }
        """

    @pg.production("stmt : stmt IF_MOD expr_value")
    def stmt_ifmod(self, p):
        """
        stmt kIF_MOD expr_value {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($3), $1, null);
                }
        """

    @pg.production("stmt : stmt UNLESS_MOD expr_value")
    def stmt_unlessmod(self, p):
        """
        stmt kUNLESS_MOD expr_value {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($3), null, $1);
                }
        """

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

    @pg.production("stmt : stmt RESCUE_MOD stmt")
    def stmt_rescue_mod(self, p):
        """
        stmt kRESCUE_MOD stmt {
                    Node body = $3 == null ? NilImplicitNode.NIL : $3;
                    $$ = new RescueNode(support.getPosition($1), $1, new RescueBodyNode(support.getPosition($1), null, body, null), null);
                }
        """

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

    @pg.production("stmt : primary_value LITERAL_LBRACKET opt_call_args rbracket OP_ASGN command_call")
    def stmt_subscript_op_asgn_command_call(self, p):
        """
        primary_value '[' opt_call_args rbracket tOP_ASGN command_call {
  // FIXME: arg_concat logic missing for opt_call_args
                    $$ = support.new_opElementAsgnNode(support.getPosition($1), $1, (String) $5.getValue(), $3, $6);
                }
        """

    @pg.production("stmt : primary_value DOT IDENTIFIER OP_ASGN command_call")
    def stmt_method_op_asgn_command_call(self, p):
        """
        primary_value tDOT tIDENTIFIER tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """

    @pg.production("stmt : primary_value DOT CONSTANT OP_ASGN command_call")
    def stmt_method_constant_op_asgn_command_call(self, p):
        """
        primary_value tDOT tCONSTANT tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """

    @pg.production("stmt : primary_value COLON2 IDENTIFIER OP_ASGN command_call")
    def stmt_constant_op_asgn_command_call(self, p):
        """
        primary_value tCOLON2 tIDENTIFIER tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """

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

    @pg.production("stmt : mlhs LITERAL_EQUAL arg_value")
    def stmt_mlhs_equal_arg_value(self, p):
        """
        mlhs '=' arg_value {
                    $1.setValueNode($3);
                    $$ = $1;
                }
        """

    @pg.production("stmt : mlhs LITERAL_EQUAL mrhs")
    def stmt_mlhs_equal_mrhs(self, p):
        """
        mlhs '=' mrhs {
                    $<AssignableNode>1.setValueNode($3);
                    $$ = $1;
                    $1.setPosition(support.getPosition($1));
                }
        """

    @pg.production("stmt : expr")
    def stmt_expr(self, p):
        return p[0]

    @pg.production("command_asgn : lhs LITERAL_EQUAL command_call")
    def command_asgn_lhs_equal_command_call(self, p):
        """
        lhs '=' command_call {
                    support.checkExpression($3);
                    $$ = support.node_assign($1, $3);
                }
        """

    @pg.production("command_asgn : lhs LITERAL_EQUAL command_asgn")
    def command_asgn_lhs_equal_command_asgn(self, p):
        """
        lhs '=' command_asgn {
                    support.checkExpression($3);
                    $$ = support.node_assign($1, $3);
                }
        """

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

    @pg.production("expr : BAND command_call")
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

    @pg.production("block_command : block_call COLON2 operation2 command_args")
    def block_command_colon(self, p):
        """
        block_call tCOLON2 operation2 command_args {
                    $$ = support.new_call($1, $3, $4, null);
                }

        """

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

    @pg.production("command : operation command_args", precedence="LOWEST")
    def command_operation_command_args(self, p):
        """
        operation command_args %prec tLOWEST {
                    $$ = support.new_fcall($1, $2, null);
                }
        """

    @pg.production("command : operation command_args cmd_brace_block")
    def command_operation_command_args_cmd_brace_block(self, p):
        """
        operation command_args cmd_brace_block {
                    $$ = support.new_fcall($1, $2, $3);
                }
        """

    @pg.production("command : primary_value DOT operation2 command_args", precedence="LOWEST")
    def command_method_call_args(self, p):
        """
        primary_value tDOT operation2 command_args %prec tLOWEST {
                    $$ = support.new_call($1, $3, $4, null);
                }
        """

    @pg.production("command : primary_value DOT operation2 command_args cmd_brace_block")
    def command_method_call_args_brace_block(self, p):
        """
        primary_value tDOT operation2 command_args cmd_brace_block {
                    $$ = support.new_call($1, $3, $4, $5);
                }
        """

    @pg.production("command : primary_value COLON2 operation2 command_args", precedence="LOWEST")
    def command_colon_call_args(self, p):
        """
        primary_value tCOLON2 operation2 command_args %prec tLOWEST {
                    $$ = support.new_call($1, $3, $4, null);
                }
        """

    @pg.production("command : primary_value COLON2 operation2 command_args cmd_brace_block")
    def command_colon_call_args_brace_block(self, p):
        """
        primary_value tCOLON2 operation2 command_args cmd_brace_block {
                    $$ = support.new_call($1, $3, $4, $5);
                }
        """

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

    @pg.production("mlhs_basic : mlhs_head")
    def mlhs_basic_mlhs_head(self, p):
        """
        mlhs_head {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, null, null);
                }
        """

    @pg.production("mlhs_basic : mlhs_head mlhs_item")
    def mlhs_basic_mlhs_head_mlhs_item(self, p):
        """
        mlhs_head mlhs_item {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1.add($2), null, null);
                }
        """

    @pg.production("mlhs_basic : mlhs_head STAR mlhs_node")
    def mlhs_basic_mlhs_head_star_node(self, p):
        """
        mlhs_head tSTAR mlhs_node {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, $3, (ListNode) null);
                }
        """

    @pg.production("mlhs_basic : mlhs_head STAR mlhs_node LITERAL_COMMA mlhs_post")
    def mlhs_basic_mlhs_head_star_node_comma_post(self, p):
        """
        mlhs_head tSTAR mlhs_node ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, $3, $5);
                }
        """

    @pg.production("mlhs_basic : mlhs_head STAR")
    def mlhs_basic_mlhs_head_star(self, p):
        """
        mlhs_head tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), null);
                }
        """

    @pg.production("mlhs_basic : mlhs_head STAR LITERAL_COMMA mlhs_post")
    def mlhs_basic_mlhs_head_star_comma_post(self, p):
        """
        mlhs_head tSTAR ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), $4);
                }
        """

    @pg.production("mlhs_basic : STAR mlhs_node")
    def mlhs_basic_star_mlhs_node(self, p):
        """
        tSTAR mlhs_node {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, $2, null);
                }
        """

    @pg.production("mlhs_basic : STAR mlhs_node LITERAL_COMMA mlhs_post")
    def mlhs_basic_star_mlhs_node_comma_post(self, p):
        """
        tSTAR mlhs_node ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, $2, $4);
                }
        """

    @pg.production("mlhs_basic : STAR")
    def mlhs_basic_star(self, p):
        """
        tSTAR {
                      $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), null);
                }
        """

    @pg.production("mlhs_basic : STAR LITERAL_COMMA mlhs_post")
    def mlhs_basic_star_comma_post(self, p):
        """
        tSTAR ',' mlhs_post {
                      $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), $3);
                }
        """

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

    @pg.production("mlhs_node : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def mlhs_node_subscript(self, p):
        """
        primary_value '[' opt_call_args rbracket {
                    $$ = support.aryset($1, $3);
                }
        """

    @pg.production("mlhs_node : primary_value DOT IDENTIFIER")
    def mlhs_node_attr(self, p):
        """
        primary_value tDOT tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """

    @pg.production("mlhs_node : primary_value COLON2 IDENTIFIER")
    def mlhs_node_colon_attr(self, p):
        """
        primary_value tCOLON2 tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """

    @pg.production("mlhs_node : primary_value DOT CONSTANT")
    def mlhs_node_attr_constant(self, p):
        """
        primary_value tDOT tCONSTANT {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """

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

    @pg.production("mlhs_node : backref")
    def mlhs_node_backref(self, p):
        """
        backref {
                    support.backrefAssignError($1);
                }
        """

    @pg.production("lhs : variable")
    def lhs_variable(self, p):
        """
        variable {
                      // if (!($$ = assignable($1, 0))) $$ = NEW_BEGIN(0);
                    $$ = support.assignable($1, NilImplicitNode.NIL);
                }
        """

    @pg.production("lhs : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def lhs_subscript(self, p):
        """
        primary_value '[' opt_call_args rbracket {
                    $$ = support.aryset($1, $3);
                }
        """

    @pg.production("lhs : primary_value DOT IDENTIFIER")
    def lhs_dot_identifier(self, p):
        """
        primary_value tDOT tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """

    @pg.production("lhs : primary_value COLON2 IDENTIFIER")
    def lhs_colon_identifier(self, p):
        """
        primary_value tCOLON2 tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """

    @pg.production("lhs : primary_value DOT CONSTANT")
    def lhs_dot_constant(self, p):
        """
        primary_value tDOT tCONSTANT {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
        """

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

    @pg.production("cpath : cname")
    def cpath_cname(self, p):
        """
        cname {
                    $$ = support.new_colon2($1.getPosition(), null, (String) $1.getValue());
                }
        """

    @pg.production("cpath : primary_value COLON2 cname")
    def cpath_colon_cname(self, p):
        """
        primary_value tCOLON2 cname {
                    $$ = support.new_colon2(support.getPosition($1), $1, (String) $3.getValue());
                }
        """

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
        """
        fname {
                    $$ = new LiteralNode($1);
                }
        """

    @pg.production("fsym : symbol")
    def fsym_symbol(self, p):
        """
        symbol {
                    $$ = new LiteralNode($1);
                }
        """

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

    @pg.production("undef_list : undef_list LITERAL_COMMA fitem")
    def undef_list_undef_list(self, p):
        """
        undef_list ',' {
                    lexer.setState(LexState.EXPR_FNAME);
                } fitem {
                    $$ = support.appendToBlock($1, support.newUndef($1.getPosition(), $4));
                }
        """

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

    @pg.production("arg : lhs LITERAL_EQUAL arg RESCUE_MOD arg")
    def arg_lhs_equal_arg_rescue_mod(self, p):
        """
        lhs '=' arg kRESCUE_MOD arg {
                    ISourcePosition position = $4.getPosition();
                    Node body = $5 == null ? NilImplicitNode.NIL : $5;
                    $$ = support.node_assign($1, new RescueNode(position, $3, new RescueBodyNode(position, null, body, null), null));
                }
        """

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

    @pg.production("arg : primary_value LITERAL_LBRACKET opt_call_args rbracket OP_ASGN arg")
    def arg_subscript_op_asgn_arg(self, p):
        """
        primary_value '[' opt_call_args rbracket tOP_ASGN arg {
  // FIXME: arg_concat missing for opt_call_args
                    $$ = support.new_opElementAsgnNode(support.getPosition($1), $1, (String) $5.getValue(), $3, $6);
                }
        """

    @pg.production("arg : primary_value DOT IDENTIFIER OP_ASGN arg")
    def arg_method_op_asgn_arg(self, p):
        """
        primary_value tDOT tIDENTIFIER tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """

    @pg.production("arg : primary_value DOT CONSTANT OP_ASGN arg")
    def arg_method_constant_op_asgn_arg(self, p):
        """
        primary_value tDOT tCONSTANT tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """

    @pg.production("arg : primary_value COLON2 IDENTIFIER OP_ASGN arg")
    def arg_colon_method_op_asgn_arg(self, p):
        """
        primary_value tCOLON2 tIDENTIFIER tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
        """

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

    @pg.production("arg : UMINUS_NUM FLOAT POW arg")
    def arg_uminus_num_float_pow_arg(self, p):
        """
        tUMINUS_NUM tFLOAT tPOW arg {
                    $$ = support.getOperatorCallNode(support.getOperatorCallNode($2, "**", $4, lexer.getPosition()), "-@");
                }
        """

    @pg.production("arg : UMINUS arg")
    @pg.production("arg : UPLUS arg")
    def arg_uplus_arg(self, p):
        return self.new_unary_call(p[0], p[1])

    @pg.production("arg : arg NEQ arg")
    @pg.production("arg : arg EQQ arg")
    @pg.production("arg : arg EQ arg")
    @pg.production("arg : arg LEQ")
    @pg.production("arg : arg LT")
    @pg.production("arg : arg GEQ")
    @pg.production("arg : arg GT arg")
    @pg.production("arg : arg CMP arg")
    @pg.production("arg : arg AMPER2 arg")
    @pg.production("arg : arg CARET arg")
    @pg.production("arg : arg PIPE arg")
    def arg_binop2(self, p):
        return self.new_binary_call(p[0], p[1], p[2])

    @pg.production("arg : arg MATCH arg")
    def arg_match_arg(self, p):
        """
        arg tMATCH arg {
                    $$ = support.getMatchNode($1, $3);
                  /* ENEBO
                        $$ = match_op($1, $3);
                        if (nd_type($1) == NODE_LIT && TYPE($1->nd_lit) == T_REGEXP) {
                            $$ = reg_named_capture_assign($1->nd_lit, $$);
                        }
                  */
                }
        """

    @pg.production("arg : arg NMATCH arg")
    def arg_nmatch_arg(self, p):
        """
        arg tNMATCH arg {
                    $$ = support.getOperatorCallNode($1, "!~", $3, lexer.getPosition());
                }
        """

    @pg.production("arg : BANG arg")
    def arg_bang_arg(self, p):
        """
        tBANG arg {
                    $$ = support.getOperatorCallNode(support.getConditionNode($2), "!");
                }
        """

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

    @pg.production("arg : arg LITERAL_QUESTION_MARK arg opt_nl LITERAL_COLON arg")
    def arg_ternary(self, p):
        """
        arg '?' arg opt_nl ':' arg {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($1), $3, $6);
                }
        """

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

    @pg.production("aref_args : assocs trailer")
    def aref_args_assocs_trailer(self, p):
        """
        assocs trailer {
                    $$ = support.newArrayNode($1.getPosition(), new Hash19Node(lexer.getPosition(), $1));
                }
        """

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

    @pg.production("call_args : args opt_block_arg")
    def call_args_args_opt_block_arg(self, p):
        """
        args opt_block_arg {
                    $$ = support.arg_blk_pass($1, $2);
                }
        """

    @pg.production("call_args : assocs opt_block_arg")
    def call_args_assocs_opt_block_arg(self, p):
        """
        assocs opt_block_arg {
                    $$ = support.newArrayNode($1.getPosition(), new Hash19Node(lexer.getPosition(), $1));
                    $$ = support.arg_blk_pass((Node)$$, $2);
                }
        """

    @pg.production("call_args : args LITERAL_COMMA assocs opt_block_arg")
    def call_args_args_comma_assocs_opt_block_arg(self, p):
        """
        args ',' assocs opt_block_arg {
                    $$ = support.arg_append($1, new Hash19Node(lexer.getPosition(), $3));
                    $$ = support.arg_blk_pass((Node)$$, $4);
                }
        """

    @pg.production("call_args : block_arg")
    def call_args_block_arg(self, p):
        """
        block_arg {
                }
        """

    @pg.production("command_args : call_args")
    def command_args(self, p):
        """
        /* none */ {
                    $$ = Long.valueOf(lexer.getCmdArgumentState().begin());
                } call_args {
                    lexer.getCmdArgumentState().reset($<Long>1.longValue());
                    $$ = $2;
                }
        """

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
        """
        arg_value {
                    ISourcePosition pos = $1 == null ? lexer.getPosition() : $1.getPosition();
                    $$ = support.newArrayNode(pos, $1);
                }
        """

    @pg.production("args : STAR arg_value")
    def args_star_arg_value(self, p):
        """
        tSTAR arg_value {
                    $$ = support.newSplatNode($1.getPosition(), $2);
                }
        """

    @pg.production("args : args LITERAL_COMMA arg_value")
    def args_comma_arg_value(self, p):
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

    @pg.production("args : args LITERAL_COMMA STAR arg_value")
    def args_comma_star_arg_value(self, p):
        """
        args ',' tSTAR arg_value {
                    Node node = null;

                    // FIXME: lose syntactical elements here (and others like this)
                    if ($4 instanceof ArrayNode &&
                        (node = support.splat_array($1)) != null) {
                        $$ = support.list_concat(node, $4);
                    } else {
                        $$ = support.arg_concat(support.getPosition($1), $1, $4);
                    }
                }
        """

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

    @pg.production("mrhs : STAR arg_value")
    def mrhs_star_arg_value(self, p):
        """
        tSTAR arg_value {
                     $$ = support.newSplatNode(support.getPosition($1), $2);
                }
        """

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

    @pg.production("primary : BEGIN bodystmt END")
    def primary_begin_end(self, p):
        """
        kBEGIN bodystmt kEND {
                    $$ = new BeginNode(support.getPosition($1), $2 == null ? NilImplicitNode.NIL : $2);
                }
        """

    @pg.production("primary : LPAREN_ARG expr rparen")
    def primary_paren_arg(self, p):
        """
        tLPAREN_ARG expr {
                    lexer.setState(LexState.EXPR_ENDARG);
                } rparen {
                    support.warning(ID.GROUPED_EXPRESSION, $1.getPosition(), "(...) interpreted as grouped expression");
                    $$ = $2;
                }
        """

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

    @pg.production("primary : primary_value COLON2 CONSTANT")
    def primary_constant_lookup(self, p):
        """
        primary_value tCOLON2 tCONSTANT {
                    $$ = support.new_colon2(support.getPosition($1), $1, (String) $3.getValue());
                }
        """

    @pg.production("primary : COLON3 CONSTANT")
    def primary_unbound_constant(self, p):
        """
        tCOLON3 tCONSTANT {
                    $$ = support.new_colon3($1.getPosition(), (String) $2.getValue());
                }
        """

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

    @pg.production("primary : LBRACE assoc_list RCURLY")
    def primary_hash(self, p):
        """
        tLBRACE assoc_list tRCURLY {
                    $$ = new Hash19Node($1.getPosition(), $2);
                }
        """

    @pg.production("primary : RETURN")
    def primary_return(self, p):
        """
        kRETURN {
                    $$ = new ReturnNode($1.getPosition(), NilImplicitNode.NIL);
                }
        """

    @pg.production("primary : YIELD LPAREN2 call_args rparen")
    def primary_yield_paren_args(self, p):
        """
        kYIELD tLPAREN2 call_args rparen {
                    $$ = support.new_yield($1.getPosition(), $3);
                }
        """

    @pg.production("primary : YIELD LPAREN2 rparen")
    def primary_yield_paren(self, p):
        """
        kYIELD tLPAREN2 rparen {
                    $$ = new ZYieldNode($1.getPosition());
                }
        """

    @pg.production("primary : YIELD")
    def primary_yield(self, p):
        """
        kYIELD {
                    $$ = new ZYieldNode($1.getPosition());
                }
        """

    @pg.production("primary : DEFINED opt_nl LPAREN2 expr rparen")
    def primary_defined(self, p):
        """
        kDEFINED opt_nl tLPAREN2 expr rparen {
                    $$ = new DefinedNode($1.getPosition(), $4);
                }
        """

    @pg.production("primary : NOT LPAREN2 expr rparen")
    def primary_not_paren_expr(self, p):
        """
        kNOT tLPAREN2 expr rparen {
                    $$ = support.getOperatorCallNode(support.getConditionNode($3), "!");
                }
        """

    @pg.production("primary : NOT LPAREN2 rparen")
    def primary_not_paren(self, p):
        """
        kNOT tLPAREN2 rparen {
                    $$ = support.getOperatorCallNode(NilImplicitNode.NIL, "!");
                }
        """

    @pg.production("primary : operation brace_block")
    def primary_operation_brace_block(self, p):
        """
        operation brace_block {
                    $$ = new FCallNoArgBlockNode($1.getPosition(), (String) $1.getValue(), $2);
                }
        """

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

    @pg.production("primary : LAMBDA lambda")
    def primary_lambda(self, p):
        return p[0]

    @pg.production("primary : IF expr_value then compstmt if_tail END")
    def primary_if(self, p):
        """
        kIF expr_value then compstmt if_tail kEND {
                    $$ = new IfNode($1.getPosition(), support.getConditionNode($2), $4, $5);
                }
        """

    @pg.production("primary : UNLESS expr_value then compstmt opt_else END")
    def primary_unless(self, p):
        """
        kUNLESS expr_value then compstmt opt_else kEND {
                    $$ = new IfNode($1.getPosition(), support.getConditionNode($2), $5, $4);
                }
        """

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

    @pg.production("primary : UNTIL expr_Value do compstmt END")
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

    @pg.production("primary : CASE expr_value opt_terms case_body END")
    def primary_case_expr_value(self, p):
        """
        kCASE expr_value opt_terms case_body kEND {
                    $$ = support.newCaseNode($1.getPosition(), $2, $4);
                }
        """

    @pg.production("primary : CASE opt_terms case_body END")
    def primary_case(self, p):
        """
        kCASE opt_terms case_body kEND {
                    $$ = support.newCaseNode($1.getPosition(), null, $3);
                }
        """

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

    @pg.production("primary : BREAK")
    def primary_break(self, p):
        """
        kBREAK {
                    $$ = new BreakNode($1.getPosition(), NilImplicitNode.NIL);
                }
        """

    @pg.production("primary : NEXT")
    def primary_next(self, p):
        """
        kNEXT {
                    $$ = new NextNode($1.getPosition(), NilImplicitNode.NIL);
                }
        """

    @pg.production("primary : REDO")
    def primary_redo(self, p):
        """
        kREDO {
                    $$ = new RedoNode($1.getPosition());
                }
        """

    @pg.production("primary : RETRY")
    def primary_retry(self, p):
        """
        kRETRY {
                    $$ = new RetryNode($1.getPosition());
                }
        """

    @pg.production("primary_value : primary")
    def primary_value(self, p):
        """
        primary {
                    support.checkExpression($1);
                    $$ = $1;
                    if ($$ == null) $$ = NilImplicitNode.NIL;
                }
        """

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
        """
        kELSIF expr_value then compstmt if_tail {
                    $$ = new IfNode($1.getPosition(), support.getConditionNode($2), $4, $5);
                }
        """

    @pg.production("opt_else : none")
    def opt_else_none(self, p):
        return p[0]

    @pg.production("opt_else : ELSE compstmt")
    def opt_else(self, p):
        return p[1]

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

    @pg.production("f_arg : LPAREN f_margs rparen")
    def f_marg_paren(self, p):
        return p[1]

    @pg.production("f_marg_list : f_marg")
    def f_marg_list_f_marg(self, p):
        """
        f_marg {
                    $$ = support.newArrayNode($1.getPosition(), $1);
                }
        """

    @pg.production("f_marg_list : f_marg_list LITERAL_COMMA f_marg")
    def f_marg_list(self, p):
        """
        f_marg_list ',' f_marg {
                    $$ = $1.add($3);
                }
        """

    @pg.production("f_margs : f_marg_list")
    def f_margs_f_marg_list(self, p):
        """
        f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, null, null);
                }
        """

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR f_norm_arg")
    def f_margs_f_marg_list_comma_star_f_norm_Arg(self, p):
        """
        f_marg_list ',' tSTAR f_norm_arg {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, support.assignable($4, null), null);
                }
        """

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR f_norm_arg COMMA f_marg_list")
    def f_margs_f_marg_list_comma_star_f_norm_arg_comm_f_marg_list(self, p):
        """
        f_marg_list ',' tSTAR f_norm_arg ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, support.assignable($4, null), $6);
                }
        """

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR")
    def f_margs_f_marg_list_comma_star(self, p):
        """
        f_marg_list ',' tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), null);
                }
        """

    @pg.production("f_margs : f_marg_list LITERAL_COMMA STAR LITERAL_COMMA f_marg_list")
    def f_margs_f_marg_list_comma_star_comma_f_marg_list(self, p):
        """
        f_marg_list ',' tSTAR ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), $5);
                }
        """

    @pg.production("f_margs : STAR f_norm_arg")
    def f_margs_star_f_norm_arg(self, p):
        """
        tSTAR f_norm_arg {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, support.assignable($2, null), null);
                }
        """

    @pg.production("f_margs : STAR f_norm_arg LITERAL_COMMA f_marg_list")
    def f_margs_star_f_norm_arg_comma_f_marg_list(self, p):
        """
        tSTAR f_norm_arg ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, support.assignable($2, null), $4);
                }
        """

    @pg.production("f_margs : STAR")
    def f_margs_star(self, p):
        """
        tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), null);
                }
        """

    @pg.production("f_margs : STAR LITERAL_COMMA f_marg_list")
    def f_margs_star_comma_f_marg_list(self, p):
        """
        tSTAR ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, null, $3);
                }
        """

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_block_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, null, $6);
                }
        """

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_block_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, $7, $8);
                }
        """

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_block_optarg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, null, $4);
                }
        """

    @pg.production("block_param : f_arg LITERAL_COMMA f_block_optarg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_block_optarg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_block_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, $5, $6);
                }
        """

    @pg.production("block_param : f_arg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, null, $4);
                }
        """

    @pg.production("block_param : f_arg LITERAL_COMMA")
    def block_param_f_arg_comma(self, p):
        """
        f_arg ',' {
                    RestArgNode rest = new UnnamedRestArgNode($1.getPosition(), null, support.getCurrentScope().addVariable("*"));
                    $$ = support.new_args($1.getPosition(), $1, null, rest, null, null);
                }
        """

    @pg.production("block_param : f_arg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_arg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_arg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, $5, $6);
                }
        """

    @pg.production("block_param : f_arg opt_f_block_arg")
    def block_param_f_arg_opt_f_block_arg(self, p):
        """
        f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, null, null, $2);
                }
        """

    @pg.production("block_param : f_block_optarg LITERAL_COMMA f_rest_arg opt_f_block_arg")
    def block_param_f_block_optarg_comma_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_block_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, $3, null, $4);
                }
        """

    @pg.production("block_param : f_block_optarg LITERAL_COMMA f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_block_optarg_comma_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_block_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, $3, $5, $6);
                }
        """

    @pg.production("block_param : f_block_optarg opt_f_block_arg")
    def block_param_f_block_optarg_opt_f_block_arg(self, p):
        """
        f_block_optarg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, null, null, $2);
                }
        """

    @pg.production("block_param : f_block_optarg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_block_optarg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_block_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, null, $3, $4);
                }
        """

    @pg.production("block_param : f_rest_arg opt_f_block_arg")
    def block_param_f_rest_arg_opt_f_block_arg(self, p):
        """
        f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, $1, null, $2);
                }
        """

    @pg.production("block_param : f_rest_arg LITERAL_COMMA f_arg opt_f_block_arg")
    def block_param_f_rest_arg_comma_f_arg_opt_f_block_arg(self, p):
        """
        f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, $1, $3, $4);
                }
        """

    @pg.production("block_param : f_block_arg")
    def block_param_f_block_arg(self, p):
        """
        f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, $1);
                }
        """

    @pg.production("opt_block_param : none")
    def opt_block_param_none(self, p):
        """
        none {
    // was $$ = null;
                   $$ = support.new_args(lexer.getPosition(), null, null, null, null, null);
                }
        """

    @pg.production("opt_block_param : block_param_def")
    def opt_block_param(self, p):
        """
        block_param_def {
                    lexer.commandStart = true;
                    $$ = $1;
                }
        """

    @pg.production("block_param_def : PIPE opt_bv_decl PIPE")
    def block_param_def_pipe_opt_bv_decl_pipe(self, p):
        """
        tPIPE opt_bv_decl tPIPE {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, null);
                }
        """

    @pg.production("block_param_def : OROP")
    def block_param_def_orop(self, p):
        """
        tOROP {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, null);
                }
        """

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

    @pg.production("block_arg : block_call DOT operation2 opt_paren_args")
    def block_call_dot_operation_opt_paren_args(self, p):
        """
        block_call tDOT operation2 opt_paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
        """

    @pg.production("block_call : block_call COLON2 operation2 opt_paren_args")
    def block_call_colon_operation_opt_paren_args(self, p):
        """
        block_call tCOLON2 operation2 opt_paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }

        """

    @pg.production("method_call : operation paren_args")
    def method_call_operation_paren_args(self, p):
        """
        operation paren_args {
                    $$ = support.new_fcall($1, $2, null);
                }
        """

    @pg.production("method_call : primary_value DOT operation2 opt_paren_args")
    def method_call_primary_value_dot_operation_opt_paren_args(self, p):
        """
        primary_value tDOT operation2 opt_paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
        """

    @pg.production("method_call : primary_value COLON2 operation2 paren_args")
    def method_call_primary_value_colon_operation_paren_args(self, p):
        """
        primary_value tCOLON2 operation2 paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
        """

    @pg.production("method_call : primary_value COLON2 operation3")
    def method_call_primary_value_colon_operation(self, p):
        """
        primary_value tCOLON2 operation3 {
                    $$ = support.new_call($1, $3, null, null);
                }
        """

    @pg.production("method_call : primary_value DOT paren_args")
    def method_call_primary_value_dot_paren_args(self, p):
        """
        primary_value tDOT paren_args {
                    $$ = support.new_call($1, new Token("call", $1.getPosition()), $3, null);
                }
        """

    @pg.production("method_call : primary_value COLON2 paren_args")
    def method_call_primary_value_colon_paren_args(self, p):
        """
        primary_value tCOLON2 paren_args {
                    $$ = support.new_call($1, new Token("call", $1.getPosition()), $3, null);
                }
        """

    @pg.production("method_call : SUPER paren_args")
    def method_call_super_paren_args(self, p):
        """
        kSUPER paren_args {
                    $$ = support.new_super($2, $1);
                }
        """

    @pg.production("method_call : SUPER")
    def method_call_super(self, p):
        """
        kSUPER {
                    $$ = new ZSuperNode($1.getPosition());
                }
        """

    @pg.production("method_call : primary_value LITERAL_LBRACKET opt_call_args rbracket")
    def method_call_primary_value_lbracket_opt_call_args_rbracket(self, p):
        """
        primary_value '[' opt_call_args rbracket {
                    if ($1 instanceof SelfNode) {
                        $$ = support.new_fcall(new Token("[]", support.getPosition($1)), $3, null);
                    } else {
                        $$ = support.new_call($1, new Token("[]", support.getPosition($1)), $3, null);
                    }
                }
        """

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

    @pg.production("case_body : WHEN args then compstmt cases")
    def case_body(self, p):
        """
        kWHEN args then compstmt cases {
                    $$ = support.newWhenNode($1.getPosition(), $2, $4, $5);
                }
        """

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

    @pg.production("exc_list : mrhs")
    def exc_list_mrhs(self, p):
        """
        mrhs {
                    $$ = support.splat_array($1);
                    if ($$ == null) $$ = $1;
                }
        """

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
        """
        symbol {
                    // FIXME: We may be intern'ing more than once.
                    $$ = new SymbolNode($1.getPosition(), ((String) $1.getValue()).intern());
                }
        """

    @pg.production("literal : dsym")
    def literal_dsym(self, p):
        return p[0]

    @pg.production("strings : string")
    def strings(self, p):
        """
        string {
                    $$ = $1 instanceof EvStrNode ? new DStrNode($1.getPosition(), lexer.getEncoding()).add($1) : $1;
                    /*
                    NODE *node = $1;
                    if (!node) {
                        node = NEW_STR(STR_NEW0());
                    } else {
                        node = evstr2dstr(node);
                    }
                    $$ = node;
                    */
                }
        """

    @pg.production("string : CHAR")
    def string_char(self, p):
        """
        tCHAR {
                    ByteList aChar = ByteList.create((String) $1.getValue());
                    aChar.setEncoding(lexer.getEncoding());
                    $$ = lexer.createStrNode($<Token>0.getPosition(), aChar, 0);
                }
        """

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

    @pg.production("regexp : REGEXP_BEG xstring_contents REGEXP_END")
    def regexp(self, p):
        """
        tREGEXP_BEG xstring_contents tREGEXP_END {
                    $$ = support.newRegexpNode($1.getPosition(), $2, (RegexpNode) $3);
                }
        """

    @pg.production("words : WORDS_BEG LITERAL_SPACE STRING_END")
    def words_space(self, p):
        """
        tWORDS_BEG ' ' tSTRING_END {
                    $$ = new ZArrayNode($1.getPosition());
                }
        """

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

    @pg.production("word_list : word_list word LITERAL_SPACE")
    def word_list(self, p):
        """
        word_list word ' ' {
                     $$ = $1.add($2 instanceof EvStrNode ? new DStrNode($1.getPosition(), lexer.getEncoding()).add($2) : $2);
                }
        """

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

    @pg.production("qwords : QWORDS_BEG LITERAL_SPACE STRING_END")
    def qwords_space(self, p):
        """
        tQWORDS_BEG ' ' tSTRING_END {
                     $$ = new ZArrayNode($1.getPosition());
                }
        """

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
    
    @pg.production("qword_list : qword_list STRING_CONTENT LITERAL_SPACE")
    def qword_list(self, p):
        """
        qword_list tSTRING_CONTENT ' ' {
                    $$ = $1.add($2);
                }
        """

    """
string_contents : /* none */ {
                    ByteList aChar = ByteList.create("");
                    aChar.setEncoding(lexer.getEncoding());
                    $$ = lexer.createStrNode($<Token>0.getPosition(), aChar, 0);
                }
                | string_contents string_content {
                    $$ = support.literal_concat($1.getPosition(), $1, $2);
                }

xstring_contents: /* none */ {
                    $$ = null;
                }
                | xstring_contents string_content {
                    $$ = support.literal_concat(support.getPosition($1), $1, $2);
                }

string_content  : tSTRING_CONTENT {
                    $$ = $1;
                }
                | tSTRING_DVAR {
                    $$ = lexer.getStrTerm();
                    lexer.setStrTerm(null);
                    lexer.setState(LexState.EXPR_BEG);
                } string_dvar {
                    lexer.setStrTerm($<StrTerm>2);
                    $$ = new EvStrNode($1.getPosition(), $3);
                }
                | tSTRING_DBEG {
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

string_dvar     : tGVAR {
                     $$ = new GlobalVarNode($1.getPosition(), (String) $1.getValue());
                }
                | tIVAR {
                     $$ = new InstVarNode($1.getPosition(), (String) $1.getValue());
                }
                | tCVAR {
                     $$ = new ClassVarNode($1.getPosition(), (String) $1.getValue());
                }
                | backref

// Token:symbol
symbol          : tSYMBEG sym {
                     lexer.setState(LexState.EXPR_END);
                     $$ = $2;
                     $<ISourcePositionHolder>$.setPosition($1.getPosition());
                }

// Token:symbol
sym             : fname | tIVAR | tGVAR | tCVAR

dsym            : tSYMBEG xstring_contents tSTRING_END {
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

numeric         : tINTEGER {
                    $$ = $1;
                }
                | tFLOAT {
                     $$ = $1;
                }
                | tUMINUS_NUM tINTEGER %prec tLOWEST {
                     $$ = support.negateInteger($2);
                }
                | tUMINUS_NUM tFLOAT %prec tLOWEST {
                     $$ = support.negateFloat($2);
                }

// [!null]
variable        : tIDENTIFIER | tIVAR | tGVAR | tCONSTANT | tCVAR
                | kNIL {
                    $$ = new Token("nil", Tokens.kNIL, $1.getPosition());
                }
                | kSELF {
                    $$ = new Token("self", Tokens.kSELF, $1.getPosition());
                }
                | kTRUE {
                    $$ = new Token("true", Tokens.kTRUE, $1.getPosition());
                }
                | kFALSE {
                    $$ = new Token("false", Tokens.kFALSE, $1.getPosition());
                }
                | k__FILE__ {
                    $$ = new Token("__FILE__", Tokens.k__FILE__, $1.getPosition());
                }
                | k__LINE__ {
                    $$ = new Token("__LINE__", Tokens.k__LINE__, $1.getPosition());
                }
                | k__ENCODING__ {
                    $$ = new Token("__ENCODING__", Tokens.k__ENCODING__, $1.getPosition());
                }

// [!null]
var_ref         : variable {
                    $$ = support.gettable($1);
                }

// [!null]
var_lhs         : variable {
                    $$ = support.assignable($1, NilImplicitNode.NIL);
                }

// [!null]
backref         : tNTH_REF {
                    $$ = $1;
                }
                | tBACK_REF {
                    $$ = $1;
                }

superclass      : term {
                    $$ = null;
                }
                | tLT {
                   lexer.setState(LexState.EXPR_BEG);
                } expr_value term {
                    $$ = $3;
                }
                | error term {
                   $$ = null;
                }

// [!null]
// ENEBO: Look at command_start stuff I am ripping out
f_arglist       : tLPAREN2 f_args rparen {
                    $$ = $2;
                    $<ISourcePositionHolder>$.setPosition($1.getPosition());
                    lexer.setState(LexState.EXPR_BEG);
                }
                | f_args term {
                    $$ = $1;
                }

// [!null]
f_args          : f_arg ',' f_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, null, $6);
                }
                | f_arg ',' f_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, $7, $8);
                }
                | f_arg ',' f_optarg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, null, $4);
                }
                | f_arg ',' f_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, $5, $6);
                }
                | f_arg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, null, $4);
                }
                | f_arg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, $5, $6);
                }
                | f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, null, null, $2);
                }
                | f_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, $3, null, $4);
                }
                | f_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, $3, $5, $6);
                }
                | f_optarg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, null, null, $2);
                }
                | f_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, $1, null, $3, $4);
                }
                | f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, $1, null, $2);
                }
                | f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, $1, $3, $4);
                }
                | f_block_arg {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, $1);
                }
                | /* none */ {
                    $$ = support.new_args(lexer.getPosition(), null, null, null, null, null);
                }

f_bad_arg       : tCONSTANT {
                    support.yyerror("formal argument cannot be a constant");
                }
                | tIVAR {
                    support.yyerror("formal argument cannot be an instance variable");
                }
                | tGVAR {
                    support.yyerror("formal argument cannot be a global variable");
                }
                | tCVAR {
                    support.yyerror("formal argument cannot be a class variable");
                }

// Token:f_norm_arg [!null]
f_norm_arg      : f_bad_arg
                | tIDENTIFIER {
                    $$ = support.formal_argument($1);
                }

f_arg_item      : f_norm_arg {
                    $$ = support.arg_var($1);
  /*
                    $$ = new ArgAuxiliaryNode($1.getPosition(), (String) $1.getValue(), 1);
  */
                }
                | tLPAREN f_margs rparen {
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

// [!null]
f_arg           : f_arg_item {
                    $$ = new ArrayNode(lexer.getPosition(), $1);
                }
                | f_arg ',' f_arg_item {
                    $1.add($3);
                    $$ = $1;
                }

f_opt           : tIDENTIFIER '=' arg_value {
                    support.arg_var(support.formal_argument($1));
                    $$ = new OptArgNode($1.getPosition(), support.assignable($1, $3));
                }

f_block_opt     : tIDENTIFIER '=' primary_value {
                    support.arg_var(support.formal_argument($1));
                    $$ = new OptArgNode($1.getPosition(), support.assignable($1, $3));
                }

f_block_optarg  : f_block_opt {
                    $$ = new BlockNode($1.getPosition()).add($1);
                }
                | f_block_optarg ',' f_block_opt {
                    $$ = support.appendToBlock($1, $3);
                }

f_optarg        : f_opt {
                    $$ = new BlockNode($1.getPosition()).add($1);
                }
                | f_optarg ',' f_opt {
                    $$ = support.appendToBlock($1, $3);
                }

restarg_mark    : tSTAR2 | tSTAR

// [!null]
f_rest_arg      : restarg_mark tIDENTIFIER {
                    if (!support.is_local_id($2)) {
                        support.yyerror("rest argument must be local variable");
                    }

                    $$ = new RestArgNode(support.arg_var(support.shadowing_lvar($2)));
                }
                | restarg_mark {
                    $$ = new UnnamedRestArgNode($1.getPosition(), "", support.getCurrentScope().addVariable("*"));
                }

// [!null]
blkarg_mark     : tAMPER2 | tAMPER

// f_block_arg - Block argument def for function (foo(&block)) [!null]
f_block_arg     : blkarg_mark tIDENTIFIER {
                    if (!support.is_local_id($2)) {
                        support.yyerror("block argument must be local variable");
                    }

                    $$ = new BlockArgNode(support.arg_var(support.shadowing_lvar($2)));
                }

opt_f_block_arg : ',' f_block_arg {
                    $$ = $2;
                }
                | /* none */ {
                    $$ = null;
                }

singleton       : var_ref {
                    if (!($1 instanceof SelfNode)) {
                        support.checkExpression($1);
                    }
                    $$ = $1;
                }
                | tLPAREN2 {
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

// [!null]
assoc_list      : none {
                    $$ = new ArrayNode(lexer.getPosition());
                }
                | assocs trailer {
                    $$ = $1;
                }

// [!null]
assocs          : assoc
                | assocs ',' assoc {
                    $$ = $1.addAll($3);
                }

// [!null]
assoc           : arg_value tASSOC arg_value {
                    ISourcePosition pos;
                    if ($1 == null && $3 == null) {
                        pos = $2.getPosition();
                    } else {
                        pos = $1.getPosition();
                    }

                    $$ = support.newArrayNode(pos, $1).add($3);
                }
                | tLABEL arg_value {
                    ISourcePosition pos = $1.getPosition();
                    $$ = support.newArrayNode(pos, new SymbolNode(pos, (String) $1.getValue())).add($2);
                }

operation       : tIDENTIFIER | tCONSTANT | tFID
operation2      : tIDENTIFIER | tCONSTANT | tFID | op
operation3      : tIDENTIFIER | tFID | op
dot_or_colon    : tDOT | tCOLON2
opt_terms       : /* none */ | terms
opt_nl          : /* none */ | '\n'
rparen          : opt_nl tRPAREN {
                    $$ = $2;
                }
rbracket        : opt_nl tRBRACK {
                    $$ = $2;
                }
trailer         : /* none */ | '\n' | ','

term            : ';'
                | '\n'

terms           : term
                | terms ';'

none            : /* none */ {
                      $$ = null;
                }

none_block_pass : /* none */ {
                  $$ = null;
                }


    """
    parser = pg.build()


class LexerWrapper(object):
    def __init__(self, lexer):
        self.lexer = lexer

    def next(self):
        try:
            return self.lexer.next()
        except StopIteration:
            return None
