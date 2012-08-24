from pypy.rlib.rstring import StringBuilder

from rply import ParserGenerator
from rply.token import BaseBox

from rupypy import ast


class LexerWrapper(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self.token_iter = iter(lexer)

    def next(self):
        try:
            return self.token_iter.next()
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

    def getlist(self):
        return self.nodes


pg = ParserGenerator([
    "EOF", "NEWLINE", "SEMICOLON", "COMMA", "DOT", "LBRACKET", "RBRACKET",
    "LSUBSCRIPT", "LPAREN", "RPAREN", "EXCLAMATION",

    "AND_LITERAL", "OR_LITERAL", "NOT_LITERAL", "IF", "DEF", "END", "THEN",

    "NUMBER",

    "STRING_BEG", "STRING_END", "STRING_CONTENT", "CHAR", "REGEXP_BEG",
    "REGEXP_END", "SYMBOL_BEG",

    "IDENTIFIER", "GLOBAL", "INSTANCE_VAR",

    "PLUS", "MINUS", "MUL", "DIV", "MODULO", "POW", "LSHIFT", "RSHIFT", "AMP",
    "PIPE", "CARET", "EQEQ", "NE", "EQEQEQ", "LT", "LE", "GT", "GE", "CMP",
    "EQUAL_TILDE", "EXCLAMATION_TILDE", "UNARY_STAR"
], precedence=[
    ("nonassoc", ["LOWEST"]),
    ("left", ["OR_LITERAL", "AND_LITERAL"]),
    ("right", ["NOT_LITERAL"]),
    ("left", ["OR"]),
    ("left", ["AND"]),
    ("nonassoc", ["CMP", "EQ", "EQEQ", "EQEQEQ", "NE", "EQUAL_TILDE", "EXCLAMATION_TILDE"]),
    ("left", ["GT", "GE", "LT", "LE"]),
    ("left", ["PIPE", "CARET"]),
    ("left", ["AMP"]),
    ("left", ["LSHIFT", "RSHIFT"]),
    ("left", ["PLUS", "MINUS"]),
    ("left", ["MUL", "DIV", "MODULO"]),
    ("right", ["UMINUS"]),
    ("right", ["POW"]),
    ("right", ["EXCLAMATION", "TILDE", "UPLUS"]),
])


@pg.production("program : top_compstmt EOF")
def program(p):
    return BoxAST(ast.Main(p[0].getast()))


@pg.production("top_compstmt : top_stmts opt_terms")
def top_compstmt(p):
    return BoxAST(ast.Block(p[0].getlist()))


@pg.production("top_stmts : top_stmt")
def top_stmts_top_stmt(p):
    return BoxASTList([p[0].getast()])


@pg.production("top_stmts : top_stmts terms top_stmt")
def top_stmts(p):
    return BoxASTList(p[0].getlist() + [p[2].getast()])


@pg.production("top_stmts : none")
def top_stmts_none(p):
    return BoxASTList([])


@pg.production("top_stmt : stmt")
def top_stmt(p):
    return p[0]

"""
top_stmt      : klBEGIN {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("BEGIN in method");
                    }
              } tLCURLY top_compstmt tRCURLY {
                    support.getResult().addBeginNode(new PreExe19Node($1.getPosition(), support.getCurrentScope(), $4));
                    $$ = null;
              }
"""


@pg.production("bodystmt : compstmt opt_rescue opt_else opt_ensure")
def bodystmt(p):
    return p[0]


@pg.production("compstmt : stmts opt_terms")
def compstmt(p):
    return BoxAST(ast.Block(p[0].getlist()))


@pg.production("stmts : none")
def stmts_none(p):
    return BoxASTList([])


@pg.production("stmts : stmt")
def stmts_stmt(p):
    return BoxASTList([p[0].getast()])


@pg.production("stmts : stmts term stmt")
def stmts_stmts(p):
    return BoxASTList(p[0].getlist() + [p[2].getast()])

"""
stmt            : kALIAS fitem {
                    lexer.setState(LexState.EXPR_FNAME);
                } fitem {
                    $$ = support.newAlias($1.getPosition(), $2, $4);
                }
                | kALIAS tGVAR tGVAR {
                    $$ = new VAliasNode($1.getPosition(), (String) $2.getValue(), (String) $3.getValue());
                }
                | kALIAS tGVAR tBACK_REF {
                    $$ = new VAliasNode($1.getPosition(), (String) $2.getValue(), "$" + $<BackRefNode>3.getType());
                }
                | kALIAS tGVAR tNTH_REF {
                    support.yyerror("can't make alias for the number variables");
                }
                | kUNDEF undef_list {
                    $$ = $2;
                }
                | stmt kIF_MOD expr_value {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($3), $1, null);
                }
                | stmt kUNLESS_MOD expr_value {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($3), null, $1);
                }
                | stmt kWHILE_MOD expr_value {
                    if ($1 != null && $1 instanceof BeginNode) {
                        $$ = new WhileNode(support.getPosition($1), support.getConditionNode($3), $<BeginNode>1.getBodyNode(), false);
                    } else {
                        $$ = new WhileNode(support.getPosition($1), support.getConditionNode($3), $1, true);
                    }
                }
                | stmt kUNTIL_MOD expr_value {
                    if ($1 != null && $1 instanceof BeginNode) {
                        $$ = new UntilNode(support.getPosition($1), support.getConditionNode($3), $<BeginNode>1.getBodyNode(), false);
                    } else {
                        $$ = new UntilNode(support.getPosition($1), support.getConditionNode($3), $1, true);
                    }
                }
                | stmt kRESCUE_MOD stmt {
                    Node body = $3 == null ? NilImplicitNode.NIL : $3;
                    $$ = new RescueNode(support.getPosition($1), $1, new RescueBodyNode(support.getPosition($1), null, body, null), null);
                }
                | klEND tLCURLY compstmt tRCURLY {
                    if (support.isInDef() || support.isInSingle()) {
                        support.warn(ID.END_IN_METHOD, $1.getPosition(), "END in method; use at_exit");
                    }
                    $$ = new PostExeNode($1.getPosition(), $3);
                }
                | command_asgn
                | mlhs '=' command_call {
                    support.checkExpression($3);
                    $1.setValueNode($3);
                    $$ = $1;
                }
                | var_lhs tOP_ASGN command_call {
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
                | primary_value '[' opt_call_args rbracket tOP_ASGN command_call {
  // FIXME: arg_concat logic missing for opt_call_args
                    $$ = support.new_opElementAsgnNode(support.getPosition($1), $1, (String) $5.getValue(), $3, $6);
                }
                | primary_value tDOT tIDENTIFIER tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
                | primary_value tDOT tCONSTANT tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
                | primary_value tCOLON2 tIDENTIFIER tOP_ASGN command_call {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
                | backref tOP_ASGN command_call {
                    support.backrefAssignError($1);
                }
                | lhs '=' mrhs {
                    $$ = support.node_assign($1, $3);
                }
                | mlhs '=' arg_value {
                    $1.setValueNode($3);
                    $$ = $1;
                }
                | mlhs '=' mrhs {
                    $<AssignableNode>1.setValueNode($3);
                    $$ = $1;
                    $1.setPosition(support.getPosition($1));
                }
"""


@pg.production("stmt : expr")
def stmt_expr(p):
    return BoxAST(ast.Statement(p[0].getast()))

"""
command_asgn    : lhs '=' command_call {
                    support.checkExpression($3);
                    $$ = support.node_assign($1, $3);
                }
                | lhs '=' command_asgn {
                    support.checkExpression($3);
                    $$ = support.node_assign($1, $3);
                }
"""

@pg.production("expr : NOT_LITERAL opt_nl expr")
def expr_not(p):
    return BoxAST(ast.Not(p[2].getast()))


@pg.production("expr : EXCLAMATION command_call")
def expr_exclamation(p):
    return BoxAST(ast.Not(p[1].getast()))


@pg.production("expr : command_call")
def expr_command_call(p):
    return p[0]


@pg.production("expr : arg")
def expr_arg(p):
    return p[0]


@pg.production("expr : expr AND_LITERAL expr")
def expr_and(p):
    return BoxAST(ast.And(p[0].getast(), p[2].getast()))


@pg.production("expr : expr OR_LITERAL expr")
def expr_or(p):
    return BoxAST(ast.Or(p[0].getast(), p[2].getast()))


@pg.production("expr_value : expr")
def expr_value(p):
    return p[0]

"""
// Node:command - call with or with block on end [!null]
command_call    : block_command
                | kRETURN call_args {
                    $$ = new ReturnNode($1.getPosition(), support.ret_args($2, $1.getPosition()));
                }
                | kBREAK call_args {
                    $$ = new BreakNode($1.getPosition(), support.ret_args($2, $1.getPosition()));
                }
                | kNEXT call_args {
                    $$ = new NextNode($1.getPosition(), support.ret_args($2, $1.getPosition()));
                }
"""


@pg.production("command_call : command")
def command_call_command(p):
    return p[0]
"""
// Node:block_command - A call with a block (foo.bar {...}, foo::bar {...}, bar {...}) [!null]
block_command   : block_call
                | block_call tDOT operation2 command_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
                | block_call tCOLON2 operation2 command_args {
                    $$ = support.new_call($1, $3, $4, null);
                }

// :brace_block - [!null]
cmd_brace_block : tLBRACE_ARG {
                    support.pushBlockScope();
                } opt_block_param compstmt tRCURLY {
                    $$ = new IterNode($1.getPosition(), $3, $4, support.getCurrentScope());
                    support.popCurrentScope();
                }

// Node:command - fcall/call/yield/super [!null]
command        : operation command_args cmd_brace_block {
                    $$ = support.new_fcall($1, $2, $3);
                }
                | primary_value tDOT operation2 command_args cmd_brace_block {
                    $$ = support.new_call($1, $3, $4, $5);
                }
                | primary_value tCOLON2 operation2 command_args %prec tLOWEST {
                    $$ = support.new_call($1, $3, $4, null);
                }
                | primary_value tCOLON2 operation2 command_args cmd_brace_block {
                    $$ = support.new_call($1, $3, $4, $5);
                }
                | kSUPER command_args {
                    $$ = support.new_super($2, $1); // .setPosFrom($2);
                }
                | kYIELD command_args {
                    $$ = support.new_yield($1.getPosition(), $2);
                }
"""


@pg.production("command : operation command_args", precedence="LOWEST")
def command(p):
    node = ast.Send(
        ast.Self(p[0].getsourcepos().lineno),
        p[0].getstr(),
        p[1].getlist(),
        None,
        p[0].getsourcepos().lineno
    )
    return BoxAST(node)


@pg.production("command : primary_value DOT operation2 command_args", precedence="LOWEST")
def command_dot(p):
    node = ast.Send(
        p[0].getast(),
        p[2].getstr(),
        p[3].getlist(),
        None,
        p[2].getsourcepos().lineno
    )
    return BoxAST(node)

"""
// MultipleAssig19Node:mlhs - [!null]
mlhs            : mlhs_basic
                | tLPAREN mlhs_inner rparen {
                    $$ = $2;
                }

// MultipleAssign19Node:mlhs_entry - mlhs w or w/o parens [!null]
mlhs_inner      : mlhs_basic {
                    $$ = $1;
                }
                | tLPAREN mlhs_inner rparen {
                    $$ = new MultipleAsgn19Node($1.getPosition(), support.newArrayNode($1.getPosition(), $2), null, null);
                }

// MultipleAssign19Node:mlhs_basic - multiple left hand side (basic because used in multiple context) [!null]
mlhs_basic      : mlhs_head {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, null, null);
                }
                | mlhs_head mlhs_item {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1.add($2), null, null);
                }
                | mlhs_head tSTAR mlhs_node {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, $3, (ListNode) null);
                }
                | mlhs_head tSTAR mlhs_node ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, $3, $5);
                }
                | mlhs_head tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), null);
                }
                | mlhs_head tSTAR ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), $4);
                }
                | tSTAR mlhs_node {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, $2, null);
                }
                | tSTAR mlhs_node ',' mlhs_post {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, $2, $4);
                }
                | tSTAR {
                      $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), null);
                }
                | tSTAR ',' mlhs_post {
                      $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), $3);
                }

mlhs_item       : mlhs_node
                | tLPAREN mlhs_inner rparen {
                    $$ = $2;
                }

// Set of mlhs terms at front of mlhs (a, *b, d, e = arr  # a is head)
mlhs_head       : mlhs_item ',' {
                    $$ = support.newArrayNode($1.getPosition(), $1);
                }
                | mlhs_head mlhs_item ',' {
                    $$ = $1.add($2);
                }

// Set of mlhs terms at end of mlhs (a, *b, d, e = arr  # d,e is post)
mlhs_post       : mlhs_item {
                    $$ = support.newArrayNode($1.getPosition(), $1);
                }
                | mlhs_post ',' mlhs_item {
                    $$ = $1.add($3);
                }

mlhs_node       : variable {
                    $$ = support.assignable($1, NilImplicitNode.NIL);
                }
                | primary_value '[' opt_call_args rbracket {
                    $$ = support.aryset($1, $3);
                }
                | primary_value tDOT tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
                | primary_value tCOLON2 tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
                | primary_value tDOT tCONSTANT {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
                | primary_value tCOLON2 tCONSTANT {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("dynamic constant assignment");
                    }

                    ISourcePosition position = support.getPosition($1);

                    $$ = new ConstDeclNode(position, null, support.new_colon2(position, $1, (String) $3.getValue()), NilImplicitNode.NIL);
                }
                | tCOLON3 tCONSTANT {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("dynamic constant assignment");
                    }

                    ISourcePosition position = $1.getPosition();

                    $$ = new ConstDeclNode(position, null, support.new_colon3(position, (String) $2.getValue()), NilImplicitNode.NIL);
                }
                | backref {
                    support.backrefAssignError($1);
                }

lhs             : variable {
                      // if (!($$ = assignable($1, 0))) $$ = NEW_BEGIN(0);
                    $$ = support.assignable($1, NilImplicitNode.NIL);
                }
                | primary_value '[' opt_call_args rbracket {
                    $$ = support.aryset($1, $3);
                }
                | primary_value tDOT tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
                | primary_value tCOLON2 tIDENTIFIER {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
                | primary_value tDOT tCONSTANT {
                    $$ = support.attrset($1, (String) $3.getValue());
                }
                | primary_value tCOLON2 tCONSTANT {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("dynamic constant assignment");
                    }

                    ISourcePosition position = support.getPosition($1);

                    $$ = new ConstDeclNode(position, null, support.new_colon2(position, $1, (String) $3.getValue()), NilImplicitNode.NIL);
                }
                | tCOLON3 tCONSTANT {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("dynamic constant assignment");
                    }

                    ISourcePosition position = $1.getPosition();

                    $$ = new ConstDeclNode(position, null, support.new_colon3(position, (String) $2.getValue()), NilImplicitNode.NIL);
                }
                | backref {
                    support.backrefAssignError($1);
                }

cname           : tIDENTIFIER {
                    support.yyerror("class/module name must be CONSTANT");
                }
                | tCONSTANT

cpath           : tCOLON3 cname {
                    $$ = support.new_colon3($1.getPosition(), (String) $2.getValue());
                }
                | cname {
                    $$ = support.new_colon2($1.getPosition(), null, (String) $1.getValue());
                }
                | primary_value tCOLON2 cname {
                    $$ = support.new_colon2(support.getPosition($1), $1, (String) $3.getValue());
                }

// Token:fname - A function name [!null]
fname          : tCONSTANT | tFID
               | reswords {
                   lexer.setState(LexState.EXPR_ENDFN);
                   $$ = $1;
               }
"""

@pg.production("fname : op")
@pg.production("fname : IDENTIFIER")
def fname(p):
    return p[0]
"""
// LiteralNode:fsym
fsym           : fname {
                    $$ = new LiteralNode($1);
                }
                | symbol {
                    $$ = new LiteralNode($1);
                }

// Node:fitem
fitem           : fsym {
                    $$ = $1;
                }
                | dsym {
                    $$ = $1;
                }

undef_list      : fitem {
                    $$ = support.newUndef($1.getPosition(), $1);
                }
                | undef_list ',' {
                    lexer.setState(LexState.EXPR_FNAME);
                } fitem {
                    $$ = support.appendToBlock($1, support.newUndef($1.getPosition(), $4));
                }

// Token:op
op              : tPIPE | tCARET | tAMPER2 | tCMP | tEQ | tEQQ | tMATCH
                | tNMATCH | tGEQ | tLT | tLEQ | tNEQ | tLSHFT | tRSHFT
                | tPLUS | tMINUS | tSTAR2 | tSTAR | tDIVIDE | tPERCENT | tPOW
                | tBANG | tTILDE | tUPLUS | tUMINUS | tAREF | tASET | tBACK_REF2
"""
@pg.production("op : GT")
def op(p):
    return p[0]
"""
// Token:op
reswords        : k__LINE__ | k__FILE__ | k__ENCODING__ | klBEGIN | klEND
                | kALIAS | kAND | kBEGIN | kBREAK | kCASE | kCLASS | kDEF
                | kDEFINED | kDO | kELSE | kELSIF | kEND | kENSURE | kFALSE
                | kFOR | kIN | kMODULE | kNEXT | kNIL | kNOT
                | kOR | kREDO | kRESCUE | kRETRY | kRETURN | kSELF | kSUPER
                | kTHEN | kTRUE | kUNDEF | kWHEN | kYIELD
                | kIF_MOD | kUNLESS_MOD | kWHILE_MOD | kUNTIL_MOD | kRESCUE_MOD

arg             : lhs '=' arg {
                    $$ = support.node_assign($1, $3);
                    // FIXME: Consider fixing node_assign itself rather than single case
                    $<Node>$.setPosition(support.getPosition($1));
                }
                | lhs '=' arg kRESCUE_MOD arg {
                    ISourcePosition position = $4.getPosition();
                    Node body = $5 == null ? NilImplicitNode.NIL : $5;
                    $$ = support.node_assign($1, new RescueNode(position, $3, new RescueBodyNode(position, null, body, null), null));
                }
                | var_lhs tOP_ASGN arg {
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
                | var_lhs tOP_ASGN arg kRESCUE_MOD arg {
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
                | primary_value '[' opt_call_args rbracket tOP_ASGN arg {
  // FIXME: arg_concat missing for opt_call_args
                    $$ = support.new_opElementAsgnNode(support.getPosition($1), $1, (String) $5.getValue(), $3, $6);
                }
                | primary_value tDOT tIDENTIFIER tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
                | primary_value tDOT tCONSTANT tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
                | primary_value tCOLON2 tIDENTIFIER tOP_ASGN arg {
                    $$ = new OpAsgnNode(support.getPosition($1), $1, $5, (String) $3.getValue(), (String) $4.getValue());
                }
                | primary_value tCOLON2 tCONSTANT tOP_ASGN arg {
                    support.yyerror("constant re-assignment");
                }
                | tCOLON3 tCONSTANT tOP_ASGN arg {
                    support.yyerror("constant re-assignment");
                }
                | backref tOP_ASGN arg {
                    support.backrefAssignError($1);
                }
                | arg tDOT2 arg {
                    support.checkExpression($1);
                    support.checkExpression($3);

                    boolean isLiteral = $1 instanceof FixnumNode && $3 instanceof FixnumNode;
                    $$ = new DotNode(support.getPosition($1), $1, $3, false, isLiteral);
                }
                | arg tDOT3 arg {
                    support.checkExpression($1);
                    support.checkExpression($3);

                    boolean isLiteral = $1 instanceof FixnumNode && $3 instanceof FixnumNode;
                    $$ = new DotNode(support.getPosition($1), $1, $3, true, isLiteral);
                }
                | tUMINUS_NUM tINTEGER tPOW arg {
                    $$ = support.getOperatorCallNode(support.getOperatorCallNode($2, "**", $4, lexer.getPosition()), "-@");
                }
                | tUMINUS_NUM tFLOAT tPOW arg {
                    $$ = support.getOperatorCallNode(support.getOperatorCallNode($2, "**", $4, lexer.getPosition()), "-@");
                }
                | tUPLUS arg {
                    $$ = support.getOperatorCallNode($2, "+@");
                }
                | tUMINUS arg {
                    $$ = support.getOperatorCallNode($2, "-@");
                }
                | tTILDE arg {
                    $$ = support.getOperatorCallNode($2, "~");
                }
                | arg tANDOP arg {
                    $$ = support.newAndNode($2.getPosition(), $1, $3);
                }
                | arg tOROP arg {
                    $$ = support.newOrNode($2.getPosition(), $1, $3);
                }
                | kDEFINED opt_nl arg {
                    // ENEBO: arg surrounded by in_defined set/unset
                    $$ = new DefinedNode($1.getPosition(), $3);
                }
                | arg '?' arg opt_nl ':' arg {
                    $$ = new IfNode(support.getPosition($1), support.getConditionNode($1), $3, $6);
                }
"""


@pg.production("arg : arg PLUS arg")
@pg.production("arg : arg MINUS arg")
@pg.production("arg : arg MUL arg")
@pg.production("arg : arg DIV arg")
@pg.production("arg : arg MODULO arg")
@pg.production("arg : arg POW arg")
@pg.production("arg : arg LSHIFT arg")
@pg.production("arg : arg RSHIFT arg")
@pg.production("arg : arg AMP arg")
@pg.production("arg : arg PIPE arg")
@pg.production("arg : arg CARET arg")
@pg.production("arg : arg EQEQ arg")
@pg.production("arg : arg NE arg")
@pg.production("arg : arg EQEQEQ arg")
@pg.production("arg : arg LT arg")
@pg.production("arg : arg LE arg")
@pg.production("arg : arg GT arg")
@pg.production("arg : arg GE arg")
@pg.production("arg : arg CMP arg")
@pg.production("arg : arg EQUAL_TILDE arg")
def arg_binop(p):
    node = ast.BinOp(
        p[1].getstr(),
        p[0].getast(),
        p[2].getast(),
        p[1].getsourcepos().lineno
    )
    return BoxAST(node)


@pg.production("arg : EXCLAMATION arg")
def arg_exclamation(p):
    return BoxAST(ast.Not(p[1].getast()))


@pg.production("arg : arg EXCLAMATION_TILDE arg")
def arg_not_match(p):
    node = ast.Not(
        ast.BinOp(
            "=~",
            p[0].getast(),
            p[2].getast(),
            p[1].getsourcepos().lineno
        )
    )
    return BoxAST(node)


@pg.production("arg : primary")
def arg_primary(p):
    return p[0]


@pg.production("arg_value : arg")
def arg_value(p):
    return p[0]

"""
aref_args       : args ',' assocs trailer {
                    $$ = support.arg_append($1, new Hash19Node(lexer.getPosition(), $3));
                }
                | assocs trailer {
                    $$ = support.newArrayNode($1.getPosition(), new Hash19Node(lexer.getPosition(), $1));
                }
"""


@pg.production("aref_args : none")
def aref_args_empty(p):
    return BoxASTList([])


@pg.production("aref_args : args trailer")
def aref_args_args(p):
    return p[0]

@pg.production("paren_args : LPAREN opt_call_args rparen")
def paren_args(p):
    return p[1]


@pg.production("opt_paren_args : none")
def opt_paren_args_none(p):
    return BoxASTList([])


@pg.production("opt_paren_args : paren_args")
def opt_paren_args(p):
    return p[0]


@pg.production("opt_call_args : none")
def opt_call_args_none(p):
    return BoxASTList([])


@pg.production("opt_call_args : call_args")
def opt_call_args(p):
    return p[0]
"""
// [!null]
call_args       : args opt_block_arg {
                    $$ = support.arg_blk_pass($1, $2);
                }
                | assocs opt_block_arg {
                    $$ = support.newArrayNode($1.getPosition(), new Hash19Node(lexer.getPosition(), $1));
                    $$ = support.arg_blk_pass((Node)$$, $2);
                }
                | args ',' assocs opt_block_arg {
                    $$ = support.arg_append($1, new Hash19Node(lexer.getPosition(), $3));
                    $$ = support.arg_blk_pass((Node)$$, $4);
                }
                | block_arg {
                }

"""


@pg.production("call_args : command")
def call_args_command(p):
    return BoxASTList([p[0].getast()])


@pg.production("call_args : args opt_block_arg")
def call_args_args(p):
    return p[0]


@pg.production("command_args : none")
def command_args_empty(p):
    return None


@pg.production("command_args : call_args")
def command_args(p):
    return p[0]
"""
block_arg       : tAMPER arg_value {
                    $$ = new BlockPassNode($1.getPosition(), $2);
                }

opt_block_arg   : ',' block_arg {
                    $$ = $2;
                }
                | ',' {
                    $$ = null;
                }
"""
@pg.production("opt_block_arg : none_block_pass")
def opt_block_arg_none(p):
    return None


@pg.production("args : arg_value")
def args_arg(p):
    return BoxASTList([p[0].getast()])


@pg.production("args : UNARY_STAR arg_value")
def args_splat_arg(p):
    return BoxASTList([ast.Splat(p[1].getast())])


@pg.production("args : args COMMA arg_value")
def args_args(p):
    return BoxASTList(p[0].getlist() + [p[2].getast()])


@pg.production("args : args COMMA UNARY_STAR arg_value")
def args_args_splat(p):
    return BoxASTList(p[0].getlist() + [ast.Splat(p[3].getast())])
"""
mrhs            : args ',' arg_value {
                    Node node = support.splat_array($1);

                    if (node != null) {
                        $$ = support.list_append(node, $3);
                    } else {
                        $$ = support.arg_append($1, $3);
                    }
                }
                | args ',' tSTAR arg_value {
                    Node node = null;

                    if ($4 instanceof ArrayNode &&
                        (node = support.splat_array($1)) != null) {
                        $$ = support.list_concat(node, $4);
                    } else {
                        $$ = support.arg_concat($1.getPosition(), $1, $4);
                    }
                }
                | tSTAR arg_value {
                     $$ = support.newSplatNode(support.getPosition($1), $2);
                }

primary         : xstring
                | words
                | qwords
                | backref
                | tFID {
                    $$ = new FCallNoArgNode($1.getPosition(), (String) $1.getValue());
                }
                | kBEGIN bodystmt kEND {
                    $$ = new BeginNode(support.getPosition($1), $2 == null ? NilImplicitNode.NIL : $2);
                }
                | tLPAREN_ARG expr {
                    lexer.setState(LexState.EXPR_ENDARG);
                } rparen {
                    support.warning(ID.GROUPED_EXPRESSION, $1.getPosition(), "(...) interpreted as grouped expression");
                    $$ = $2;
                }
                | primary_value tCOLON2 tCONSTANT {
                    $$ = support.new_colon2(support.getPosition($1), $1, (String) $3.getValue());
                }
                | tCOLON3 tCONSTANT {
                    $$ = support.new_colon3($1.getPosition(), (String) $2.getValue());
                }
                | tLBRACE assoc_list tRCURLY {
                    $$ = new Hash19Node($1.getPosition(), $2);
                }
                | kRETURN {
                    $$ = new ReturnNode($1.getPosition(), NilImplicitNode.NIL);
                }
                | kYIELD tLPAREN2 call_args rparen {
                    $$ = support.new_yield($1.getPosition(), $3);
                }
                | kYIELD tLPAREN2 rparen {
                    $$ = new ZYieldNode($1.getPosition());
                }
                | kYIELD {
                    $$ = new ZYieldNode($1.getPosition());
                }
                | kDEFINED opt_nl tLPAREN2 expr rparen {
                    $$ = new DefinedNode($1.getPosition(), $4);
                }
                | kNOT tLPAREN2 expr rparen {
                    $$ = support.getOperatorCallNode(support.getConditionNode($3), "!");
                }
                | kNOT tLPAREN2 rparen {
                    $$ = support.getOperatorCallNode(NilImplicitNode.NIL, "!");
                }
                | operation brace_block {
                    $$ = new FCallNoArgBlockNode($1.getPosition(), (String) $1.getValue(), $2);
                }
                | method_call brace_block {
                    if ($1 != null &&
                          $<BlockAcceptingNode>1.getIterNode() instanceof BlockPassNode) {
                        throw new SyntaxException(PID.BLOCK_ARG_AND_BLOCK_GIVEN, $1.getPosition(), lexer.getCurrentLine(), "Both block arg and actual block given.");
                    }
                    $$ = $<BlockAcceptingNode>1.setIterNode($2);
                    $<Node>$.setPosition($1.getPosition());
                }
                | tLAMBDA lambda {
                    $$ = $2;
                }
                | kUNLESS expr_value then compstmt opt_else kEND {
                    $$ = new IfNode($1.getPosition(), support.getConditionNode($2), $5, $4);
                }
                | kWHILE {
                    lexer.getConditionState().begin();
                } expr_value do {
                    lexer.getConditionState().end();
                } compstmt kEND {
                    Node body = $6 == null ? NilImplicitNode.NIL : $6;
                    $$ = new WhileNode($1.getPosition(), support.getConditionNode($3), body);
                }
                | kUNTIL {
                  lexer.getConditionState().begin();
                } expr_value do {
                  lexer.getConditionState().end();
                } compstmt kEND {
                    Node body = $6 == null ? NilImplicitNode.NIL : $6;
                    $$ = new UntilNode($1.getPosition(), support.getConditionNode($3), body);
                }
                | kCASE expr_value opt_terms case_body kEND {
                    $$ = support.newCaseNode($1.getPosition(), $2, $4);
                }
                | kCASE opt_terms case_body kEND {
                    $$ = support.newCaseNode($1.getPosition(), null, $3);
                }
                | kFOR for_var kIN {
                    lexer.getConditionState().begin();
                } expr_value do {
                    lexer.getConditionState().end();
                } compstmt kEND {
                      // ENEBO: Lots of optz in 1.9 parser here
                    $$ = new ForNode($1.getPosition(), $2, $8, $5, support.getCurrentScope());
                }
                | kCLASS cpath superclass {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("class definition in method body");
                    }
                    support.pushLocalScope();
                } bodystmt kEND {
                    Node body = $5 == null ? NilImplicitNode.NIL : $5;

                    $$ = new ClassNode($1.getPosition(), $<Colon3Node>2, support.getCurrentScope(), body, $3);
                    support.popCurrentScope();
                }
                | kCLASS tLSHFT expr {
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
                | kMODULE cpath {
                    if (support.isInDef() || support.isInSingle()) {
                        support.yyerror("module definition in method body");
                    }
                    support.pushLocalScope();
                } bodystmt kEND {
                    Node body = $4 == null ? NilImplicitNode.NIL : $4;

                    $$ = new ModuleNode($1.getPosition(), $<Colon3Node>2, support.getCurrentScope(), body);
                    support.popCurrentScope();
                }
                | kDEF singleton dot_or_colon {
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
                | kBREAK {
                    $$ = new BreakNode($1.getPosition(), NilImplicitNode.NIL);
                }
                | kNEXT {
                    $$ = new NextNode($1.getPosition(), NilImplicitNode.NIL);
                }
                | kREDO {
                    $$ = new RedoNode($1.getPosition());
                }
                | kRETRY {
                    $$ = new RetryNode($1.getPosition());
                }
"""


@pg.production("primary : literal")
def primary_literal(p):
    return p[0]


@pg.production("primary : var_ref")
def primary_var_ref(p):
    return p[0]


@pg.production("primary : strings")
def primary_strings(p):
    return p[0]


@pg.production("primary : regexp")
def primary_regexp(p):
    return p[0]


@pg.production("primary : LPAREN compstmt RPAREN")
def primary_parens(p):
    return p[1]


@pg.production("primary : method_call")
def primary_method_call(p):
    return p[0]


@pg.production("primary : LBRACKET aref_args RBRACKET")
def primary_array(p):
    return BoxAST(ast.Array(p[1].getlist()))


@pg.production("primary : DEF fname f_arglist bodystmt END")
def primary_def(p):
    node = ast.Function(
        None,
        p[1].getstr(),
        p[2].getlist(),
        None,
        None,
        p[3].getast()
    )
    return BoxAST(node)


@pg.production("primary : IF expr_value then compstmt if_tail END")
def primary_if(p):
    node = ast.If(
        p[1].getast(),
        p[3].getast(),
        p[4].getast()
    )
    return BoxAST(node)


@pg.production("primary_value : primary")
def primary_value(p):
    return p[0]


@pg.production("then : term THEN")
@pg.production("then : THEN")
@pg.production("then : term")
def then(p):
    return None

"""
do              : term
                | kDO_COND

if_tail         : kELSIF expr_value then compstmt if_tail {
                    $$ = new IfNode($1.getPosition(), support.getConditionNode($2), $4, $5);
                }
"""


@pg.production("if_tail : opt_else")
def if_tail_else(p):
    return p[0]

"""
opt_else        : kELSE compstmt {
                    $$ = $2;
                }
"""


@pg.production("opt_else : none")
def opt_else_none(p):
    return BoxAST(ast.Block([]))
"""
for_var         : lhs
                | mlhs {
                }

f_marg          : f_norm_arg {
                     $$ = support.assignable($1, NilImplicitNode.NIL);
                }
                | tLPAREN f_margs rparen {
                    $$ = $2;
                }

// [!null]
f_marg_list     : f_marg {
                    $$ = support.newArrayNode($1.getPosition(), $1);
                }
                | f_marg_list ',' f_marg {
                    $$ = $1.add($3);
                }

f_margs         : f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, null, null);
                }
                | f_marg_list ',' tSTAR f_norm_arg {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, support.assignable($4, null), null);
                }
                | f_marg_list ',' tSTAR f_norm_arg ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, support.assignable($4, null), $6);
                }
                | f_marg_list ',' tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), null);
                }
                | f_marg_list ',' tSTAR ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), $1, new StarNode(lexer.getPosition()), $5);
                }
                | tSTAR f_norm_arg {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, support.assignable($2, null), null);
                }
                | tSTAR f_norm_arg ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, support.assignable($2, null), $4);
                }
                | tSTAR {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, new StarNode(lexer.getPosition()), null);
                }
                | tSTAR ',' f_marg_list {
                    $$ = new MultipleAsgn19Node($1.getPosition(), null, null, $3);
                }

// [!null]
block_param     : f_arg ',' f_block_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, null, $6);
                }
                | f_arg ',' f_block_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, $5, $7, $8);
                }
                | f_arg ',' f_block_optarg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, null, $4);
                }
                | f_arg ',' f_block_optarg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, $3, null, $5, $6);
                }
                | f_arg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, null, $4);
                }
                | f_arg ',' {
                    RestArgNode rest = new UnnamedRestArgNode($1.getPosition(), null, support.getCurrentScope().addVariable("*"));
                    $$ = support.new_args($1.getPosition(), $1, null, rest, null, null);
                }
                | f_arg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, $3, $5, $6);
                }
                | f_arg opt_f_block_arg {
                    $$ = support.new_args($1.getPosition(), $1, null, null, null, $2);
                }
                | f_block_optarg ',' f_rest_arg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, $3, null, $4);
                }
                | f_block_optarg ',' f_rest_arg ',' f_arg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, $3, $5, $6);
                }
                | f_block_optarg opt_f_block_arg {
                    $$ = support.new_args(support.getPosition($1), null, $1, null, null, $2);
                }
                | f_block_optarg ',' f_arg opt_f_block_arg {
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

opt_block_param : none {
    // was $$ = null;
                   $$ = support.new_args(lexer.getPosition(), null, null, null, null, null);
                }
                | block_param_def {
                    lexer.commandStart = true;
                    $$ = $1;
                }

block_param_def : tPIPE opt_bv_decl tPIPE {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, null);
                }
                | tOROP {
                    $$ = support.new_args($1.getPosition(), null, null, null, null, null);
                }
                | tPIPE block_param opt_bv_decl tPIPE {
                    $$ = $2;
                }

// shadowed block variables....
opt_bv_decl     : opt_nl {
                    $$ = null;
                }
                | opt_nl ';' bv_decls opt_nl {
                    $$ = null;
                }

// ENEBO: This is confusing...
bv_decls        : bvar {
                    $$ = null;
                }
                | bv_decls ',' bvar {
                    $$ = null;
                }

bvar            : tIDENTIFIER {
                    support.new_bv($1);
                }
                | f_bad_arg {
                    $$ = null;
                }

lambda          : /* none */  {
                    support.pushBlockScope();
                    $$ = lexer.getLeftParenBegin();
                    lexer.setLeftParenBegin(lexer.incrementParenNest());
                } f_larglist lambda_body {
                    $$ = new LambdaNode($2.getPosition(), $2, $3, support.getCurrentScope());
                    support.popCurrentScope();
                    lexer.setLeftParenBegin($<Integer>1);
                }

f_larglist      : tLPAREN2 f_args opt_bv_decl tRPAREN {
                    $$ = $2;
                    $<ISourcePositionHolder>$.setPosition($1.getPosition());
                }
                | f_args opt_bv_decl {
                    $$ = $1;
                }

lambda_body     : tLAMBEG compstmt tRCURLY {
                    $$ = $2;
                }
                | kDO_LAMBDA compstmt kEND {
                    $$ = $2;
                }

do_block        : kDO_BLOCK {
                    support.pushBlockScope();
                } opt_block_param compstmt kEND {
                    $$ = new IterNode(support.getPosition($1), $3, $4, support.getCurrentScope());
                    support.popCurrentScope();
                }

block_call      : command do_block {
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
                | block_call tDOT operation2 opt_paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
                | block_call tCOLON2 operation2 opt_paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }

// [!null]
method_call     : primary_value tCOLON2 operation2 paren_args {
                    $$ = support.new_call($1, $3, $4, null);
                }
                | primary_value tCOLON2 operation3 {
                    $$ = support.new_call($1, $3, null, null);
                }
                | primary_value tDOT paren_args {
                    $$ = support.new_call($1, new Token("call", $1.getPosition()), $3, null);
                }
                | primary_value tCOLON2 paren_args {
                    $$ = support.new_call($1, new Token("call", $1.getPosition()), $3, null);
                }
                | kSUPER paren_args {
                    $$ = support.new_super($2, $1);
                }
                | kSUPER {
                    $$ = new ZSuperNode($1.getPosition());
                }
"""
@pg.production("method_call : operation paren_args")
def method_call_paren_args(p):
    node = ast.Send(
        ast.Self(p[0].getsourcepos().lineno),
        p[0].getstr(),
        p[1].getlist(),
        None,
        p[0].getsourcepos().lineno
    )
    return BoxAST(node)

@pg.production("method_call : primary_value DOT operation2 opt_paren_args")
def method_call_dot(p):
    node = ast.Send(
        p[0].getast(),
        p[2].getstr(),
        p[3].getlist(),
        None,
        p[2].getsourcepos().lineno
    )
    return BoxAST(node)

@pg.production("method_call : primary_value LSUBSCRIPT opt_call_args rbracket")
def method_call_subscript(p):
    node = ast.Subscript(
        p[0].getast(),
        p[2].getlist(),
        p[1].getsourcepos().lineno
    )
    return BoxAST(node)
"""
brace_block     : tLCURLY {
                    support.pushBlockScope();
                } opt_block_param compstmt tRCURLY {
                    $$ = new IterNode($1.getPosition(), $3, $4, support.getCurrentScope());
                    support.popCurrentScope();
                }
                | kDO {
                    support.pushBlockScope();
                } opt_block_param compstmt kEND {
                    $$ = new IterNode($1.getPosition(), $3, $4, support.getCurrentScope());
                    // FIXME: What the hell is this?
                    $<ISourcePositionHolder>0.setPosition(support.getPosition($<ISourcePositionHolder>0));
                    support.popCurrentScope();
                }

case_body       : kWHEN args then compstmt cases {
                    $$ = support.newWhenNode($1.getPosition(), $2, $4, $5);
                }

cases           : opt_else | case_body

opt_rescue      : kRESCUE exc_list exc_var then compstmt opt_rescue {
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


@pg.production("opt_rescue :")
def opt_rescue_none(p):
    return None
"""
exc_list        : arg_value {
                    $$ = support.newArrayNode($1.getPosition(), $1);
                }
                | mrhs {
                    $$ = support.splat_array($1);
                    if ($$ == null) $$ = $1;
                }
                | none

exc_var         : tASSOC lhs {
                    $$ = $2;
                }
                | none

opt_ensure      : kENSURE compstmt {
                    $$ = $2;
                }
"""


@pg.production("opt_ensure : none")
def opt_ensure_none(p):
    return None
"""
literal         : dsym
"""


@pg.production("literal : NUMBER")
def literal_number(p):
    s = p[0].getstr()
    if "." in s or "E" in s:
        node = ast.ConstantFloat(float(s))
    elif "X" in s:
        node = ast.ConstantInt(int(s[2:], 16))
    elif "O" in s:
        node = ast.ConstantInt(int(s[2:], 8))
    elif "B" in s:
        node = ast.ConstantInt(int(s[2:], 2))
    else:
        node = ast.ConstantInt(int(s))
    return BoxAST(node)


@pg.production("literal : symbol")
def literal_symbol(p):
    return p[0]

@pg.production("strings : string")
def strings(p):
    builder = StringBuilder()
    for node in p[0].getlist():
        if not isinstance(node, ast.ConstantString):
            break
        builder.append(node.strvalue)
    else:
        return BoxAST(ast.ConstantString(builder.build()))
    return BoxAST(ast.DynamicString(p[0].getlist()))

"""
// [!null]
string          : string string1 {
                    $$ = support.literal_concat($1.getPosition(), $1, $2);
                }
"""

@pg.production("string : CHAR")
def string_char(p):
    return BoxASTList([ast.ConstantString(p[0].getstr())])


@pg.production("string : string1")
def string_string1(p):
    return p[0]


@pg.production("string1 : STRING_BEG string_contents STRING_END")
def string1(p):
    return p[1]
"""
xstring         : tXSTRING_BEG xstring_contents tSTRING_END {
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
def regexp(p):
    builder = StringBuilder()
    for node in p[1].getlist():
        if not isinstance(node, ast.ConstantString):
            break
        builder.append(node.strvalue)
    else:
        return BoxAST(ast.ConstantRegexp(builder.build()))
    return BoxAST(ast.DynamicRegexp(p[1].getlist()))

"""
words           : tWORDS_BEG ' ' tSTRING_END {
                    $$ = new ZArrayNode($1.getPosition());
                }
                | tWORDS_BEG word_list tSTRING_END {
                    $$ = $2;
                }

word_list       : /* none */ {
                    $$ = new ArrayNode(lexer.getPosition());
                }
                | word_list word ' ' {
                     $$ = $1.add($2 instanceof EvStrNode ? new DStrNode($1.getPosition(), lexer.getEncoding()).add($2) : $2);
                }

word            : string_content
                | word string_content {
                     $$ = support.literal_concat(support.getPosition($1), $1, $2);
                }

qwords          : tQWORDS_BEG ' ' tSTRING_END {
                     $$ = new ZArrayNode($1.getPosition());
                }
                | tQWORDS_BEG qword_list tSTRING_END {
                    $$ = $2;
                    $<ISourcePositionHolder>$.setPosition($1.getPosition());
                }

qword_list      : /* none */ {
                    $$ = new ArrayNode(lexer.getPosition());
                }
                | qword_list tSTRING_CONTENT ' ' {
                    $$ = $1.add($2);
                }
"""
@pg.production("string_contents : none")
def string_contents_none(p):
    return BoxASTList([ast.ConstantString("")])


@pg.production("string_contents : string_contents string_content")
def string_contents(p):
    return BoxASTList(p[0].getlist() + [p[1].getast()])


@pg.production("xstring_contents : none")
def xstring_contents_none(p):
    return BoxASTList([])


@pg.production("xstring_contents : xstring_contents string_content")
def xstring_contents(p):
    return BoxASTList(p[0].getlist() + [p[1].getast()])

"""
string_content  : tSTRING_DVAR {
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
"""


@pg.production("string_content : STRING_CONTENT")
def string_content(p):
    return BoxAST(ast.ConstantString(p[0].getstr()))
"""
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
"""
@pg.production("symbol : SYMBOL_BEG sym")
def symbol(p):
    return BoxAST(ast.ConstantSymbol(p[1].getstr()))
"""
// Token:symbol
sym             : tIVAR | tGVAR | tCVAR
"""
@pg.production("sym : fname")
def sym(p):
    return p[0]
"""
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

// [!null]
variable        : tCONSTANT | tCVAR
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
"""

@pg.production("variable : IDENTIFIER")
def variable_identifier(p):
    return BoxAST(ast.Variable(p[0].getstr(), p[0].getsourcepos().lineno))

@pg.production("variable : GLOBAL")
def variable_global(p):
    return BoxAST(ast.Global(p[0].getstr()))

@pg.production("variable : INSTANCE_VAR")
def variable_instance_Var(p):
    return BoxAST(ast.InstanceVariable(p[0].getstr()))


@pg.production("var_ref : variable")
def var_ref(p):
    return p[0]
"""
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
"""


@pg.production("f_arglist : LPAREN f_args rparen")
def f_arglist(p):
    return p[1]


@pg.production("f_arglist : f_args term")
def f_arglist_no_paren(p):
    return p[0]
"""
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
"""


@pg.production("f_args : ")
def f_args_empty(p):
    return BoxASTList([])
"""
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
"""
@pg.production("operation : IDENTIFIER")
def operation(p):
    return p[0]
"""
operation       : tCONSTANT | tFID
operation2      : tCONSTANT | tFID | op
"""
@pg.production("operation2 : IDENTIFIER")
def operation2(p):
    return p[0]
"""
operation3      : tIDENTIFIER | tFID | op
dot_or_colon    : tDOT | tCOLON2
"""

@pg.production("opt_terms : terms")
@pg.production("opt_terms : none")
def opt_terms(p):
    return None

@pg.production("opt_nl : none")
@pg.production("opt_nl : NEWLINE")
def opt_nl(p):
    return None

@pg.production("rparen : opt_nl RPAREN")
def rparen(p):
    return None


@pg.production("rbracket : opt_nl RBRACKET")
def rbracket(p):
    return None

@pg.production("trailer : NEWLINE")
@pg.production("trailer : COMMA")
@pg.production("trailer :")
def trailer(p):
    return None

@pg.production("term : SEMICOLON")
@pg.production("term : NEWLINE")
def term(p):
    return None

@pg.production("terms : term")
@pg.production("terms : terms SEMICOLON")
def terms(p):
    return None

@pg.production("none :")
def none(p):
    return None

@pg.production("none_block_pass :")
def none_block_pass(p):
    return None

parser = pg.build()
