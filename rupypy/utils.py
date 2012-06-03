from pypy.rlib.objectmodel import specialize
from pypy.rlib.parsing.ebnfparse import (ParserBuilder, EBNFToAST,
    TransformerMaker, lexer as ebnf_lexer, parser as ebnf_parser)
from pypy.rlib.parsing.parsing import PackratParser


def make_parse_function(grammar, lexer_cls):
    visitor = ParserBuilder()
    tokens = ebnf_lexer.tokenize(grammar, True)
    s = ebnf_parser.parse(tokens)
    [s] = s.visit(EBNFToAST())
    s.visit(visitor)

    rules, changes = visitor.get_rules_and_changes()
    maker = TransformerMaker(rules, changes)
    ToASTVisitor = maker.make_transformer()

    parser = PackratParser(rules, rules[0].nonterminal)

    def parse(s):
        lexer = lexer_cls(s)
        return parser.parse(lexer.tokenize())
    return parse, ToASTVisitor


def format_traceback(space, exc):
    lines = []
    last_instr_idx = 0
    frame = exc.frame
    lines.append("%s:%d:in `%s': %s (%s)\n" % (
        frame.get_filename(),
        frame.get_lineno(exc.last_instructions[last_instr_idx]),
        frame.get_code_name(),
        exc.msg,
        space.getclass(exc).name,
    ))
    last_instr_idx += 1
    frame = frame.backref()
    while frame is not None:
        lines.append("\tfrom %s:%d:in `%s'\n" % (
            frame.get_filename(),
            frame.get_lineno(exc.last_instructions[last_instr_idx]),
            frame.get_code_name(),
        ))
        last_instr_idx += 1
        frame = frame.backref()
    return lines


class Cache(object):
    def __init__(self, space):
        self.space = space
        self.contents = {}

    @specialize.memo()
    def getorbuild(self, key):
        try:
            return self.contents[key]
        except KeyError:
            builder = self._build(key)
            self.contents[key] = builder.next()
            try:
                builder.next()
            except StopIteration:
                pass
            else:
                raise RuntimeError("generator didn't stop")
            return self.contents[key]

    def _freeze_(self):
        return True
