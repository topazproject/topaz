from pypy.rlib.parsing.ebnfparse import (ParserBuilder, EBNFToAST,
    TransformerMaker, lexer as ebnf_lexer, parser as ebnf_parser)
from pypy.rlib.parsing.parsing import PackratParser


def make_parse_function(grammar, lexer_cls):
    visitor = ParserBuilder()
    tokens = ebnf_lexer.tokenize(grammar, True)
    s = ebnf_parser.parse(tokens)
    s = s.visit(EBNFToAST())
    [s] = s
    s.visit(visitor)

    rules, changes = visitor.get_rules_and_changes()
    maker = TransformerMaker(rules, changes)
    ToASTVisitor = maker.make_transformer()

    parser = PackratParser(rules, rules[0].nonterminal)

    def parse(s):
        lexer = lexer_cls(s)
        return parser.parse(lexer.tokenize())
    return parse, ToASTVisitor
