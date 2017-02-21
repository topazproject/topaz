# coding=utf-8

from rpython.rlib.rbigint import rbigint

from topaz import ast
from topaz.utils import regexp

from .base import BaseTopazTest


class TestParser(BaseTopazTest):
    def test_empty(self, space):
        assert space.parse("") == ast.Main(ast.Nil())

    def test_int_constant(self, space):
        assert space.parse("1") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(1))
        ]))
        assert space.parse("-1") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(-1))
        ]))
        assert space.parse("1_1") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(11))
        ]))
        assert space.parse("0d10") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(10))
        ]))
        assert space.parse("0xA") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(10))
        ]))
        assert space.parse("0o10") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(8))
        ]))
        assert space.parse("0b10") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(2))
        ]))
        assert space.parse("0xbe_ef") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(48879))
        ]))
        assert space.parse("0377") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(255))
        ]))
        with self.raises(space, "SyntaxError"):
            space.parse("0378")

    def test_float(self, space):
        assert space.parse("0.2") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantFloat(0.2))
        ]))
        assert space.parse("1E1") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantFloat(10.0))
        ]))
        assert space.parse("1e1") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantFloat(10.0))
        ]))
        assert space.parse("1e-3") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantFloat(0.001))
        ]))
        assert space.parse("1e+3") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantFloat(1000.0))
        ]))
        assert space.parse("-1.2") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantFloat(-1.2))
        ]))

    def test_bignum(self, space):
        assert space.parse("18446744073709551628") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantBigInt(rbigint.fromlong(18446744073709551628)))
        ]))
        assert space.parse("-18446744073709551628") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantBigInt(rbigint.fromlong(-18446744073709551628)))
        ]))

    def test_binary_expression(self, space):
        assert space.parse("1+1") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "+", [ast.ConstantInt(1)], None, 1))
        ]))
        assert space.parse("1/1") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "/", [ast.ConstantInt(1)], None, 1))
        ]))
        assert space.parse("1===1") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "===", [ast.ConstantInt(1)], None, 1))
        ]))
        assert space.parse("2 % 3") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "%", [ast.ConstantInt(3)], None, 1))
        ]))
        assert space.parse("2 =~ 3") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "=~", [ast.ConstantInt(3)], None, 1))
        ]))
        assert space.parse("2 !~ 3") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "!~", [ast.ConstantInt(3)], None, 1))
        ]))
        assert space.parse("1 =~ /v/") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "=~", [ast.ConstantRegexp("v", 0, 1)], None, 1))
        ]))
        assert space.parse("2 & 3 | 5") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.ConstantInt(2), "&", [ast.ConstantInt(3)], None, 1), "|", [ast.ConstantInt(5)], None, 1))
        ]))
        assert space.parse("$a << []") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Global("$a"), "<<", [ast.Array([])], None, 1))
        ]))
        assert space.parse("3 >> 2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(3), ">>", [ast.ConstantInt(2)], None, 1))
        ]))
        assert space.parse("5 or 3") == ast.Main(ast.Block([
            ast.Statement(ast.Or(ast.ConstantInt(5), ast.ConstantInt(3)))
        ]))
        assert space.parse("puts 5 and 3") == ast.Main(ast.Block([
            ast.Statement(ast.And(ast.Send(ast.Self(1), "puts", [ast.ConstantInt(5)], None, 1), ast.ConstantInt(3)))
        ]))
        assert space.parse("x[0] == ?-") == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Send(ast.Send(ast.Self(1), "x", [], None, 1), "[]", [ast.ConstantInt(0)], None, 1),
                "==",
                [ast.ConstantString("-")],
                None, 1
            ))
        ]))
        assert space.parse("@x-1") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.InstanceVariable("@x"), "-", [ast.ConstantInt(1)], None, 1))
        ]))
        assert space.parse(":a <=> :a") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantSymbol("a"), "<=>", [ast.ConstantSymbol("a")], None, 1))
        ]))
        assert space.parse(":a != ?-") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantSymbol("a"), "!=", [ast.ConstantString("-")], None, 1))
        ]))
        assert space.parse("1 ^ 2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "^", [ast.ConstantInt(2)], None, 1))
        ]))
        assert space.parse("1 ** 2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "**", [ast.ConstantInt(2)], None, 1))
        ]))
        assert space.parse("-1**2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Send(ast.ConstantInt(1), "**", [ast.ConstantInt(2)], None, 1),
                "-@",
                [],
                None,
                1
            ))
        ]))
        assert space.parse("-1.0**2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Send(ast.ConstantFloat(1.0), "**", [ast.ConstantInt(2)], None, 1),
                "-@",
                [],
                None,
                1
            ))
        ]))

    def test_multi_term_expr(self, space):
        assert space.parse("1 + 2 * 3") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "+", [ast.Send(ast.ConstantInt(2), "*", [ast.ConstantInt(3)], None, 1)], None, 1))
        ]))
        assert space.parse("1 * 2 + 3") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.ConstantInt(1), "*", [ast.ConstantInt(2)], None, 1), "+", [ast.ConstantInt(3)], None, 1))
        ]))
        assert space.parse("2 << 3 * 4") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "<<", [ast.Send(ast.ConstantInt(3), "*", [ast.ConstantInt(4)], None, 1)], None, 1))
        ]))

    def test_parens(self, space):
        assert space.parse("1 * (2 - 3)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "*", [ast.Block([ast.Statement(ast.Send(ast.ConstantInt(2), "-", [ast.ConstantInt(3)], None, 1))])], None, 1))
        ]))
        assert space.parse("()") == ast.Main(ast.Block([
            ast.Statement(ast.Nil())
        ]))

    def test_multiple_statements_no_sep(self, space):
        with self.raises(space, "SyntaxError"):
            space.parse("3 3")

    def test_multiple_statements(self, space):
        r = space.parse("""
        1
        2
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(1)),
            ast.Statement(ast.ConstantInt(2)),
        ]))

    def test_multiple_statements_semicolon(self, space):
        assert space.parse("1; 2") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(1)),
            ast.Statement(ast.ConstantInt(2)),
        ]))

        assert space.parse("1; 2; 3") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(1)),
            ast.Statement(ast.ConstantInt(2)),
            ast.Statement(ast.ConstantInt(3)),
        ]))

    def test_send(self, space):
        assert space.parse("puts 2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "puts", [ast.ConstantInt(2)], None, 1))
        ]))
        assert space.parse("puts 1, 2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "puts", [ast.ConstantInt(1), ast.ConstantInt(2)], None, 1))
        ]))
        assert space.parse("puts(1, 2)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "puts", [ast.ConstantInt(1), ast.ConstantInt(2)], None, 1))
        ]))
        assert space.parse("2.to_s") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [], None, 1))
        ]))
        assert space.parse("2.to_s 10") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.ConstantInt(10)], None, 1))
        ]))
        assert space.parse("2.to_s.to_i") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.ConstantInt(2), "to_s", [], None, 1), "to_i", [], None, 1))
        ]))
        assert space.parse("2.to_s()") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [], None, 1))
        ]))
        assert space.parse("2.to_s(10)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.ConstantInt(10)], None, 1))
        ]))
        assert space.parse("2.to_s(*10)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.Splat(ast.ConstantInt(10))], None, 1))
        ]))
        assert space.parse("2.to_s(10, *x)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.ConstantInt(10), ast.Splat(ast.Send(ast.Self(1), "x", [], None, 1))], None, 1))
        ]))
        assert space.parse("2.to_s(10, :base => 5)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.ConstantInt(10), ast.Hash([(ast.ConstantSymbol("base"), ast.ConstantInt(5))])], None, 1))
        ]))
        assert space.parse("2.to_s(:base => 3)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.Hash([(ast.ConstantSymbol("base"), ast.ConstantInt(3))])], None, 1))
        ]))
        assert space.parse("2.to_s(:base=>3)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.Hash([(ast.ConstantSymbol("base"), ast.ConstantInt(3))])], None, 1))
        ]))
        assert space.parse("Integer other") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "Integer", [ast.Send(ast.Self(1), "other", [], None, 1)], None, 1))
        ]))
        assert space.parse("Module::constant") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Constant("Module", 1), "constant", [], None, 1))
        ]))
        r = space.parse("""
        nil.
            f
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Nil(), "f", [], None, 3))
        ]))

        with self.raises(space, "SyntaxError"):
            space.parse("2.to_s(:base => 5, 3)")

    def test_colon_send(self, space):
        assert space.parse("CallerSpecs::recurse(2)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Constant("CallerSpecs", 1), "recurse", [ast.ConstantInt(2)], None, 1))
        ]))

    def test_assignment(self, space):
        assert space.parse("a = 3") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("a", 1), ast.ConstantInt(3)))
        ]))
        assert space.parse("a = b = 3") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("a", 1), ast.Assignment(ast.Variable("b", 1), ast.ConstantInt(3))))
        ]))
        assert space.parse("a = method 1") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("a", 1), ast.Send(ast.Self(1), "method", [ast.ConstantInt(1)], None, 1)))
        ]))

    def test_multi_assignment(self, space):
        assert space.parse("a.x, b[:idx], c::Const, d = 3") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Send(ast.Send(ast.Self(1), "a", [], None, 1), "x", [], None, 1),
                    ast.Subscript(ast.Send(ast.Self(1), "b", [], None, 1), [ast.ConstantSymbol("idx")], 1),
                    ast.LookupConstant(ast.Send(ast.Self(1), "c", [], None, 1), "Const", 1),
                    ast.Variable("d", 1),
                ]),
                ast.ConstantInt(3)
            ))
        ]))
        assert space.parse("a = 2, 3") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("a", 1), ast.Array([ast.ConstantInt(2), ast.ConstantInt(3)])))
        ]))
        assert space.parse("a, b = split 2") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Variable("a", 1),
                    ast.Variable("b", 1),
                ]),
                ast.Send(ast.Self(1), "split", [ast.ConstantInt(2)], None, 1)
            ))
        ]))
        with self.raises(space, "SyntaxError"):
            space.parse("a, b += 3")
        assert space.parse("a, * = 1, 2") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Variable("a", 1),
                    ast.Splat(None)
                ]),
                ast.Array([
                    ast.ConstantInt(1),
                    ast.ConstantInt(2)
                ])
            ))
        ]))
        assert space.parse("a, *, b = 1, 2, 3, 4") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Variable("a", 1),
                    ast.Splat(None),
                    ast.Variable("b", 1)
                ]),
                ast.Array([
                    ast.ConstantInt(1),
                    ast.ConstantInt(2),
                    ast.ConstantInt(3),
                    ast.ConstantInt(4)
                ])
            ))
        ]))
        assert space.parse("a, *b, (c, (d, e, *), ) = 1, 2, 3, [4, [5, 6], 7]") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Variable("a", 1),
                    ast.Splat(ast.Variable("b", 1)),
                    ast.MultiAssignable([
                        ast.Variable("c", 1),
                        ast.MultiAssignable([
                            ast.Variable("d", 1),
                            ast.Variable("e", 1),
                            ast.Splat(None)
                        ]),
                    ]),
                ]),
                ast.Array([
                    ast.ConstantInt(1),
                    ast.ConstantInt(2),
                    ast.ConstantInt(3),
                    ast.Array([
                        ast.ConstantInt(4),
                        ast.Array([
                            ast.ConstantInt(5),
                            ast.ConstantInt(6)
                        ]),
                        ast.ConstantInt(7)
                    ])
                ])
            ))
        ]))

    def test_colon_attr_assignment(self, space):
        assert space.parse("a::b = nil") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Send(ast.Send(ast.Self(1), "a", [], None, 1), "b", [], None, 1), ast.Nil()))
        ]))

    def test_splat_rhs_assignment(self, space):
        assert space.parse("a,b,c = *[1,2,3]") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Variable("a", 1),
                    ast.Variable("b", 1),
                    ast.Variable("c", 1),
                ]),
                ast.Array([ast.Splat(ast.Array(
                    [
                        ast.ConstantInt(1),
                        ast.ConstantInt(2),
                        ast.ConstantInt(3),
                    ]
                ))])
            ))
        ]))
        assert space.parse("a = *[1,2,3]") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(
                ast.Variable("a", 1),
                ast.Array([ast.Splat(ast.Array(
                    [
                        ast.ConstantInt(1),
                        ast.ConstantInt(2),
                        ast.ConstantInt(3),
                    ]
                ))])
            ))
        ]))
        assert space.parse("a = 0, *[1,2,3]") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(
                ast.Variable("a", 1),
                ast.Array([
                    ast.ConstantInt(0),
                    ast.Splat(ast.Array([
                        ast.ConstantInt(1),
                        ast.ConstantInt(2),
                        ast.ConstantInt(3),
                    ])),
                ])
            ))
        ]))
        assert space.parse("a = *2, 0") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(
                ast.Variable("a", 1),
                ast.Array([
                    ast.Splat(ast.ConstantInt(2)),
                    ast.ConstantInt(0)
                ])
            ))
        ]))

    def test_splat_lhs_assignment(self, space):
        assert space.parse("a,*b,c = *[1,2]") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Variable("a", 1),
                    ast.Splat(ast.Variable("b", 1)),
                    ast.Variable("c", 1),
                ]),
                ast.Array([ast.Splat(ast.Array(
                    [
                        ast.ConstantInt(1),
                        ast.ConstantInt(2)
                    ]
                ))]),
            ))
        ]))
        assert space.parse("a, *b, c = 1") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Variable("a", 1),
                    ast.Splat(ast.Variable("b", 1)),
                    ast.Variable("c", 1),
                ]),
                ast.ConstantInt(1),
            ))
        ]))
        assert space.parse("*b,c = 1") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Splat(ast.Variable("b", 1)),
                    ast.Variable("c", 1),
                ]),
                ast.ConstantInt(1),
            ))
        ]))
        assert space.parse("b,*c = 1") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Variable("b", 1),
                    ast.Splat(ast.Variable("c", 1)),
                ]),
                ast.ConstantInt(1),
            ))
        ]))
        assert space.parse("*c = 1") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([
                    ast.Splat(ast.Variable("c", 1)),
                ]),
                ast.ConstantInt(1),
            ))
        ]))
        assert space.parse("* = 1") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([ast.Splat(None)]),
                ast.ConstantInt(1),
            ))
        ]))
        assert space.parse("a, = 3, 4") == ast.Main(ast.Block([
            ast.Statement(ast.MultiAssignment(
                ast.MultiAssignable([ast.Variable("a", 1)]),
                ast.Array([ast.ConstantInt(3), ast.ConstantInt(4)]),
            ))
        ]))
        with self.raises(space, "SyntaxError"):
            space.parse("*b, *c = 1")

    def test_load_variable(self, space):
        assert space.parse("a") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "a", [], None, 1))
        ]))

    def test_tab_indentation(self, space):
        assert space.parse("\ta") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "a", [], None, 1))
        ]))

    def test_if_statement(self, space):
        res = lambda lineno: ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3), ast.Block([
                ast.Statement(ast.Send(ast.Self(lineno), "puts", [ast.ConstantInt(2)], None, lineno))
            ]), ast.Nil()))
        ]))
        assert space.parse("if 3 then puts 2 end") == res(1)
        assert space.parse("""
        if 3
            puts 2
        end
        """) == res(3)
        assert space.parse("""
        if 3
        then
            puts 2
        end
        """) == res(4)
        assert space.parse("if 3; puts 2 end") == res(1)
        assert space.parse("if 3; end") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3), ast.Nil(), ast.Nil()))
        ]))
        r = space.parse("""
        if 0
            puts 2
            puts 3
            puts 4
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(0), ast.Block([
                ast.Statement(ast.Send(ast.Self(3), "puts", [ast.ConstantInt(2)], None, 3)),
                ast.Statement(ast.Send(ast.Self(4), "puts", [ast.ConstantInt(3)], None, 4)),
                ast.Statement(ast.Send(ast.Self(5), "puts", [ast.ConstantInt(4)], None, 5)),
            ]), ast.Nil()))
        ]))

    def test_else(self, space):
        r = space.parse("""if 3 then 5 else 4 end""")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3), ast.Block([
                ast.Statement(ast.ConstantInt(5))
            ]), ast.Block([
                ast.Statement(ast.ConstantInt(4))
            ])))
        ]))
        assert space.parse("if nil; else; end") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.Nil(), ast.Nil(), ast.Nil()))
        ]))

    def test_elsif(self, space):
        r = space.parse("""
        if 3
            5
        elsif 4 == 2
            3
        elsif 3 == 1
            2
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3), ast.Block([
                ast.Statement(ast.ConstantInt(5))
            ]), ast.If(ast.Send(ast.ConstantInt(4), "==", [ast.ConstantInt(2)], None, 4), ast.Block([
                ast.Statement(ast.ConstantInt(3))
            ]), ast.If(ast.Send(ast.ConstantInt(3), "==", [ast.ConstantInt(1)], None, 6), ast.Block([
                ast.Statement(ast.ConstantInt(2))
            ]), ast.Nil()))))
        ]))

    def test_elsif_else(self, space):
        r = space.parse("""
        if nil
            5
        elsif nil
            10
        else
            200
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.Nil(), ast.Block([
                ast.Statement(ast.ConstantInt(5))
            ]), ast.If(ast.Nil(), ast.Block([
                ast.Statement(ast.ConstantInt(10)),
            ]), ast.Block([
                ast.Statement(ast.ConstantInt(200))
            ]))))
        ]))

    def test_comparison_ops(self, space):
        assert space.parse("1 == 2; 1 < 2; 1 > 2; 1 != 2; 1 <= 2; 1 >= 2; 1 <=> 2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "==", [ast.ConstantInt(2)], None, 1)),
            ast.Statement(ast.Send(ast.ConstantInt(1), "<", [ast.ConstantInt(2)], None, 1)),
            ast.Statement(ast.Send(ast.ConstantInt(1), ">", [ast.ConstantInt(2)], None, 1)),
            ast.Statement(ast.Send(ast.ConstantInt(1), "!=", [ast.ConstantInt(2)], None, 1)),
            ast.Statement(ast.Send(ast.ConstantInt(1), "<=", [ast.ConstantInt(2)], None, 1)),
            ast.Statement(ast.Send(ast.ConstantInt(1), ">=", [ast.ConstantInt(2)], None, 1)),
            ast.Statement(ast.Send(ast.ConstantInt(1), "<=>", [ast.ConstantInt(2)], None, 1)),
        ]))

    def test_while(self, space):
        expected = ast.Main(ast.Block([
            ast.Statement(ast.While(ast.ConstantBool(True), ast.Block([
                ast.Statement(ast.Send(ast.Self(1), "puts", [ast.ConstantInt(5)], None, 1))
            ])))
        ]))
        assert space.parse("while true do puts 5 end") == expected
        assert space.parse("while true do; puts 5 end") == expected
        assert space.parse("while true; puts 5 end") == expected
        assert space.parse("while true; end") == ast.Main(ast.Block([
            ast.Statement(ast.While(ast.ConstantBool(True), ast.Nil()))
        ]))

        res = space.parse("""
        i = 0
        while i < 10 do
            puts i
            puts 1
            puts i
            puts true
        end
        """)
        assert res == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("i", 2), ast.ConstantInt(0))),
            ast.Statement(ast.While(ast.Send(ast.Variable("i", 3), "<", [ast.ConstantInt(10)], None, 3), ast.Block([
                ast.Statement(ast.Send(ast.Self(4), "puts", [ast.Variable("i", 4)], None, 4)),
                ast.Statement(ast.Send(ast.Self(5), "puts", [ast.ConstantInt(1)], None, 5)),
                ast.Statement(ast.Send(ast.Self(6), "puts", [ast.Variable("i", 6)], None, 6)),
                ast.Statement(ast.Send(ast.Self(7), "puts", [ast.ConstantBool(True)], None, 7)),
            ])))
        ]))

    def test_until(self, space):
        r = space.parse("""
        until 3
            5
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Until(ast.ConstantInt(3), ast.Block([
                ast.Statement(ast.ConstantInt(5))
            ])))
        ]))

    def test_for(self, space):
        expected = ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Array([]), "each", [], ast.SendBlock(1,
                [ast.Argument("0")], None, [], [], None, None, ast.Block([
                    ast.Statement(ast.Assignment(ast.Variable("i", 1), ast.Variable("0", 1))),
                    ast.Statement(ast.Send(ast.Self(1), "puts", [ast.Variable("i", 1)], None, 1))
                ])
            ), 1))
        ]))
        assert space.parse("for i in [] do puts i end") == expected
        assert space.parse("for i in [] do; puts i end") == expected
        assert space.parse("for i in []; puts i end") == expected
        assert space.parse("for i, in []; end") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Array([]), "each", [], ast.SendBlock(1,
                [ast.Argument("0")], None, [], [], None, None, ast.Block([
                    ast.Statement(ast.MultiAssignment(
                        ast.MultiAssignable([ast.Variable("i", 1)]),
                        ast.Variable("0", 1)
                    ))
                ])
            ), 1))
        ]))

        res = space.parse("""
        a = [0]
        for i in a
            puts i
            puts 1
            puts i
        end
        """)
        assert res == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("a", 2), ast.Array([ast.ConstantInt(0)]))),
            ast.Statement(ast.Send(ast.Variable("a", 3), "each", [], ast.SendBlock(3,
                [ast.Argument("0")], None, [], [], None, None, ast.Block([
                    ast.Statement(ast.Assignment(ast.Variable("i", 3), ast.Variable("0", 3))),
                    ast.Statement(ast.Send(ast.Self(4), "puts", [ast.Variable("i", 4)], None, 4)),
                    ast.Statement(ast.Send(ast.Self(5), "puts", [ast.ConstantInt(1)], None, 5)),
                    ast.Statement(ast.Send(ast.Self(6), "puts", [ast.Variable("i", 6)], None, 6)),
                ])
            ), 3))
        ]))

        res = space.parse("""
        for @a, *b, $c in []
        end
        """)
        assert res == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Array([]),
                "each",
                [],
                ast.SendBlock(2,
                    [ast.Argument("0")], None, [], [], None, None, ast.Block([
                        ast.Statement(ast.MultiAssignment(
                            ast.MultiAssignable([
                                ast.InstanceVariable("@a"),
                                ast.Splat(ast.Variable("b", 2)),
                                ast.Global("$c")
                            ]),
                            ast.Variable("0", 2)
                        ))
                    ])
                ),
                2
            ))
        ]))

    def test_return(self, space):
        assert space.parse("return 4") == ast.Main(ast.Block([
            ast.Return(ast.ConstantInt(4))
        ]))
        assert space.parse("return") == ast.Main(ast.Block([
            ast.Return(ast.Nil())
        ]))
        assert space.parse("return 3, 4, 5") == ast.Main(ast.Block([
            ast.Return(ast.Array([
                ast.ConstantInt(3),
                ast.ConstantInt(4),
                ast.ConstantInt(5),
            ]))
        ]))
        assert space.parse("return *3") == ast.Main(ast.Block([
            ast.Return(ast.Splat(ast.ConstantInt(3)))
        ]))
        assert space.parse("return f 1, 2") == ast.Main(ast.Block([
            ast.Return(ast.Send(ast.Self(1), "f", [ast.ConstantInt(1), ast.ConstantInt(2)], None, 1))
        ]))

    def test_array(self, space):
        assert space.parse("[]") == ast.Main(ast.Block([
            ast.Statement(ast.Array([]))
        ]))

        assert space.parse("[1, 2, 3]") == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.ConstantInt(1),
                ast.ConstantInt(2),
                ast.ConstantInt(3),
            ]))
        ]))

        assert space.parse("[[1], [2], [3]]") == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.Array([ast.ConstantInt(1)]),
                ast.Array([ast.ConstantInt(2)]),
                ast.Array([ast.ConstantInt(3)]),
            ]))
        ]))

        assert space.parse("[1, 2,]") == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.ConstantInt(1),
                ast.ConstantInt(2),
            ]))
        ]))

        r = space.parse("""
        [
            f()
        ]
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.Send(ast.Self(3), "f", [], None, 3),
            ])),
        ]))
        assert space.parse("[1, *2, *3]") == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.ConstantInt(1),
                ast.Splat(ast.ConstantInt(2)),
                ast.Splat(ast.ConstantInt(3)),
            ]))
        ]))
        assert space.parse("[:abc => 3]") == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.Hash([(ast.ConstantSymbol("abc"), ast.ConstantInt(3))])
            ]))
        ]))
        assert space.parse("[1, :abc => 3]") == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.ConstantInt(1),
                ast.Hash([(ast.ConstantSymbol("abc"), ast.ConstantInt(3))])
            ]))
        ]))

    def test_subscript(self, space):
        assert space.parse("[1][0]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Array([ast.ConstantInt(1)]), "[]", [ast.ConstantInt(0)], None, 1))
        ]))

        assert space.parse("self[i]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "[]", [ast.Send(ast.Self(1), "i", [], None, 1)], None, 1))
        ]))

        assert space.parse("self[i].to_s") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(1), "[]", [ast.Send(ast.Self(1), "i", [], None, 1)], None, 1), "to_s", [], None, 1))
        ]))

        assert space.parse("a[:a][:a]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Send(
                    ast.Send(ast.Self(1), "a", [], None, 1),
                    "[]",
                    [ast.ConstantSymbol("a")],
                    None,
                    1
                ),
                "[]",
                [ast.ConstantSymbol("a")],
                None,
                1,
            ))
        ]))
        assert space.parse("x.y[0]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Send(ast.Send(ast.Self(1), "x", [], None, 1), "y", [], None, 1),
                "[]",
                [ast.ConstantInt(0)],
                None,
                1,
            ))
        ]))
        assert space.parse("r[0, 0]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Send(ast.Self(1), "r", [], None, 1),
                "[]",
                [ast.ConstantInt(0), ast.ConstantInt(0)],
                None,
                1,
            ))
        ]))
        assert space.parse("r[]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(1), "r", [], None, 1), "[]", [], None, 1))
        ]))
        assert space.parse("f()[]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(1), "f", [], None, 1), "[]", [], None, 1))
        ]))

    def test_subscript_assginment(self, space):
        assert space.parse("x[0] = 5") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Subscript(ast.Send(ast.Self(1), "x", [], None, 1), [ast.ConstantInt(0)], 1), ast.ConstantInt(5)))
        ]))
        assert space.parse("x[] = 5") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Subscript(ast.Send(ast.Self(1), "x", [], None, 1), [], 1), ast.ConstantInt(5)))
        ]))

    def test_subscript_augmented_assignment(self, space):
        assert space.parse("x[] += 5") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("+", ast.Subscript(ast.Send(ast.Self(1), "x", [], None, 1), [], 1), ast.ConstantInt(5)))
        ]))

    def test_def(self, space):
        assert space.parse("def f() end") == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "f", [], None, [], [], None, None, ast.Nil()))
        ]))

        r = space.parse("""
        def
        f
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [], None, [], [], None, None, ast.Nil()))
        ]))

        assert space.parse("def []; end") == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "[]", [], None, [], [], None, None, ast.Nil()))
        ]))

        assert space.parse("def []=; end") == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "[]=", [], None, [], [], None, None, ast.Nil()))
        ]))

        assert space.parse("def f(a, b) a + b end") == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "f", [ast.Argument("a"), ast.Argument("b")], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Send(ast.Variable("a", 1), "+", [ast.Variable("b", 1)], None, 1))
            ])))
        ]))

        r = space.parse("""
        def f(a)
            puts a
            puts a
            puts a
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [ast.Argument("a")], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Send(ast.Self(3), "puts", [ast.Variable("a", 3)], None, 3)),
                ast.Statement(ast.Send(ast.Self(4), "puts", [ast.Variable("a", 4)], None, 4)),
                ast.Statement(ast.Send(ast.Self(5), "puts", [ast.Variable("a", 5)], None, 5)),
            ])))
        ]))

        assert space.parse("x = def f() end") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("x", 1), ast.Function(1, None, "f", [], None, [], [], None, None, ast.Nil())))
        ]))

        r = space.parse("""
        def f a, b
            a + b
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [ast.Argument("a"), ast.Argument("b")], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Send(ast.Variable("a", 3), "+", [ast.Variable("b", 3)], None, 3))
            ])))
        ]))

        r = space.parse("""
        def f(&b)
            b
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [], None, [], [], None, "b", ast.Block([
                ast.Statement(ast.Variable("b", 3))
            ])))
        ]))
        r = space.parse("""
        def f(a=nil, *b)
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [ast.Argument("a", ast.Nil())], "b", [], [], None, None, ast.Nil()))
        ]))
        r = space.parse("""
        def f(a, b=nil, *c)
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [ast.Argument("a"), ast.Argument("b", ast.Nil())], "c", [], [], None, None, ast.Nil()))
        ]))
        with self.raises(space, "SyntaxError"):
            space.parse("""
            def f(&b, a)
                b
            end
            """)
        with self.raises(space, "SyntaxError"):
            space.parse("""
            def f(&b, &c)
                b
            end
            """)

        assert space.parse("def f(*a,b,&blk); end") == ast.Main(ast.Block([
            ast.Statement(ast.Function(1,
                None,
                "f",
                [],
                "a",
                [ast.Argument("b")],
                [], None,
                "blk",
                ast.Nil()
            ))
        ]))

    def test_def_names(self, space):
        def test_name(s):
            r = space.parse("""
            def %s
            end
            """ % s)
            assert r == ast.Main(ast.Block([
                ast.Statement(ast.Function(2, None, s, [], None, [], [], None, None, ast.Nil()))
            ]))
        test_name("abc")
        test_name("<=>")
        test_name("foo=")
        test_name("===")
        test_name(">")
        test_name("<")
        test_name(">=")
        test_name("<=")
        test_name("==")
        test_name("=~")
        test_name("<<")
        test_name("-")

    def test_string(self, space):
        assert space.parse('"abc"') == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("abc"))
        ]))
        assert space.parse('"abc".size') == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantString("abc"), "size", [], None, 1))
        ]))
        assert space.parse("'abc'") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("abc"))
        ]))
        assert space.parse('"\n"') == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("\n"))
        ]))
        assert space.parse('"\\n"') == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("\n"))
        ]))
        assert space.parse("'\\n'") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("\\n"))
        ]))
        assert space.parse("?-") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("-"))
        ]))
        assert space.parse('""') == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString(""))
        ]))
        assert space.parse("'\\'<>'") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("'<>"))
        ]))
        assert space.parse('"\\"<>"') == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString('"<>'))
        ]))

    def test_escape_character(self, space):
        string = lambda content: ast.Main(ast.Block([
            ast.Statement(ast.ConstantString(content))
        ]))

        assert space.parse('?\\\\') == string("\\")
        assert space.parse('?\\n') == string("\n")
        assert space.parse('?\\t') == string("\t")
        assert space.parse('?\\r') == string("\r")
        assert space.parse('?\\f') == string("\f")
        assert space.parse('?\\v') == string("\v")
        assert space.parse('?\\a') == string("\a")
        assert space.parse('?\\b') == string("\b")
        assert space.parse('?\\e') == string("\x1b")
        assert space.parse('?\\s') == string(" ")
        assert space.parse("?\\xa") == string("\x0a")
        assert space.parse('?\\xab') == string("\xab")
        assert space.parse('?\\01') == string("\01")
        assert space.parse('?\\012') == string("\012")
        assert space.parse('?\\M-\a') == string("\x87")
        assert space.parse('?\\M-a') == string("\xe1")
        assert space.parse('?\\C-?') == string("\x7f")
        assert space.parse('?\\c?') == string("\x7f")
        assert space.parse('?\\C-\y') == string("\x19")
        assert space.parse('?\\c\y') == string("\x19")
        assert space.parse('?\\l') == string("l")
        assert space.parse('?\\0') == string("\0")
        assert space.parse('?\\01') == string("\x01")
        assert space.parse('?\\001') == string("\x01")
        assert space.parse('"\\0"') == string("\x00")
        assert space.parse('"\\01"') == string("\x01")
        assert space.parse('"\\012"') == string("\n")
        assert space.parse('"\\0\\1\\2"') == string("\x00\x01\x02")
        assert space.parse('"\\09"') == string("\x009")
        assert space.parse('"\\019"') == string("\x019")
        with self.raises(space, "SyntaxError"):
            space.parse("?\\09")
        with self.raises(space, "SyntaxError"):
            space.parse("?\\019")
        assert space.parse('?\\12') == string("\n")
        assert space.parse('"\\12"') == string("\n")
        assert space.parse('?\\012') == string("\n")
        assert space.parse('"\\342\\234\\224"') == string(u"✔".encode("utf-8"))
        assert space.parse('"\u2603"') == string(u"\u2603".encode("utf-8"))
        assert space.parse('?\u2603') == string(u"\u2603".encode("utf-8"))
        assert space.parse('"\uffff"') == string(u"\uffff".encode("utf-8"))
        assert space.parse('"\u{ff}"') == string(u"\u00ff".encode("utf-8"))
        assert space.parse('?\u{ff}') == string(u"\u00ff".encode("utf-8"))
        assert space.parse('"\u{3042 3044 3046 3048}"') == string(u"\u3042\u3044\u3046\u3048".encode("utf-8"))
        with self.raises(space, "SyntaxError", "line 1 (invalid Unicode escape)"):
            space.parse('"\u123x"')
        with self.raises(space, "SyntaxError", "line 1 (invalid Unicode escape)"):
            space.parse('"\u{}"')
        with self.raises(space, "SyntaxError", "line 1 (invalid Unicode escape)"):
            space.parse('"\u{ 3042}"')
        with self.raises(space, "SyntaxError", "line 1 (unterminated Unicode escape)"):
            space.parse('"\u{123x}"')
        with self.raises(space, "SyntaxError", "line 1 (unterminated Unicode escape)"):
            space.parse('?\u{3042 3044}')
        with self.raises(space, "SyntaxError", "line 1 (invalid Unicode codepoint (too large))"):
            space.parse('"\u{110000}"')

    def test_dynamic_string(self, space):
        const_string = lambda strvalue: ast.Main(ast.Block([
            ast.Statement(ast.ConstantString(strvalue))
        ]))
        dyn_string = lambda *components: ast.Main(ast.Block([
            ast.Statement(ast.DynamicString(list(components)))
        ]))
        assert space.parse('"#{x}"') == dyn_string(ast.Block([ast.Statement(ast.Send(ast.Self(1), "x", [], None, 1))]))
        assert space.parse('"abc #{2} abc"') == dyn_string(ast.ConstantString("abc "), ast.Block([ast.Statement(ast.ConstantInt(2))]), ast.ConstantString(" abc"))
        assert space.parse('"#{"}"}"') == dyn_string(ast.Block([ast.Statement(ast.ConstantString("}"))]))
        assert space.parse('"#{f { 2 }}"') == dyn_string(ast.Block([ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [], None, [], [], None, None, ast.Block([ast.Statement(ast.ConstantInt(2))])), 1))]))
        assert space.parse('"#{p("")}"') == dyn_string(ast.Block([ast.Statement(ast.Send(ast.Self(1), "p", [ast.ConstantString("")], None, 1))]))
        assert space.parse('"#{"#{2}"}"') == dyn_string(ast.Block([ast.Statement(ast.DynamicString([ast.Block([ast.Statement(ast.ConstantInt(2))])]))]))
        assert space.parse('"#{nil if 2}"') == dyn_string(ast.Block([ast.Statement(ast.If(
            ast.ConstantInt(2),
            ast.Block([ast.Statement(ast.Nil())]),
            ast.Nil(),
        ))]))
        assert space.parse('"\\""') == const_string('"')
        assert space.parse('"\n"') == const_string("\n")
        assert space.parse('"\w"') == const_string("w")
        assert space.parse('"\M-a"') == const_string("\xe1")
        assert space.parse('"#$abc#@a#@@ab"') == dyn_string(ast.Global("$abc"), ast.InstanceVariable("@a"), ast.ClassVariable("@@ab", 1))
        assert space.parse('"#test"') == const_string("#test")

    def test_percent_terms(self, space):
        const_string = lambda strvalue: ast.Main(ast.Block([
            ast.Statement(ast.ConstantString(strvalue))
        ]))
        dyn_string = lambda *components: ast.Main(ast.Block([
            ast.Statement(ast.DynamicString(list(components)))
        ]))
        assert space.parse('%{1}') == const_string("1")
        assert space.parse('%Q{1}') == const_string("1")
        assert space.parse('%Q{#{2}}') == dyn_string(ast.Block([ast.Statement(ast.ConstantInt(2))]))
        assert space.parse('%Q(#{2})') == dyn_string(ast.Block([ast.Statement(ast.ConstantInt(2))]))
        assert space.parse('%Q<#{2}>') == dyn_string(ast.Block([ast.Statement(ast.ConstantInt(2))]))
        assert space.parse('%Q[#{2}]') == dyn_string(ast.Block([ast.Statement(ast.ConstantInt(2))]))
        assert space.parse('%Q^#{2}^') == dyn_string(ast.Block([ast.Statement(ast.ConstantInt(2))]))
        assert space.parse('%{{}}') == const_string("{}")
        assert space.parse('%[[]]') == const_string("[]")
        assert space.parse('%<<>>') == const_string("<>")
        assert space.parse('%(())') == const_string("()")
        assert space.parse('%q{#{2}}') == const_string("#{2}")
        assert space.parse('%{\\{}') == const_string('{')
        assert space.parse('%{\\}}') == const_string('}')
        assert space.parse('%w{\ -}') == ast.Main(ast.Block([
            ast.Statement(ast.Array([ast.ConstantString(" -")]))
        ]))
        assert space.parse('%w{  hello world  }') == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.ConstantString("hello"),
                ast.ConstantString("world"),
            ]))
        ]))
        assert space.parse('%W{hello world  }') == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.ConstantString("hello"),
                ast.ConstantString("world"),
            ]))
        ]))
        assert space.parse('%w{#{"a b" + "#{\'c d\'}"}}') == ast.Main(ast.Block([
            ast.Statement(ast.Array([
                ast.ConstantString('#{"a'),
                ast.ConstantString('b"'),
                ast.ConstantString('+'),
                ast.ConstantString('"#{\'c'),
                ast.ConstantString('d\'}"}'),
            ]))
        ]))
        assert space.parse('%W{#{"a b" + "#{\'c d\'}"}}') == ast.Main(ast.Block([
            ast.Statement(ast.Array([ast.DynamicString([ast.Block([ast.Statement(
                ast.Send(
                    ast.ConstantString("a b"),
                    "+",
                    [ast.DynamicString([ast.Block([ast.Statement(ast.ConstantString("c d"))])])],
                    None,
                    1
                )
            )])])]))
        ]))
        r = space.parse("""
        %w!a!
        nil
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Array([ast.ConstantString("a")])),
            ast.Statement(ast.Nil()),
        ]))

        assert space.parse("f %q[/]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [ast.ConstantString("/")], None, 1)),
        ]))
        assert space.parse("%w[]") == ast.Main(ast.Block([
            ast.Statement(ast.Array([]))
        ]))

    def test_heredoc(self, space):
        const_heredoc = lambda s: ast.Main(ast.Block([
            ast.Statement(ast.ConstantString(s))
        ]))

        r = space.parse("""
        <<HERE
abc
HERE
        """)

        assert r == const_heredoc("abc\n")
        r = space.parse("""
        <<"HERE"
abc
HERE
        """)
        assert r == const_heredoc("abc\n")

        r = space.parse("""
        <<'HERE'
abc
HERE
        """)
        assert r == const_heredoc("abc\n")

        r = space.parse("""
        <<-HERE
        abc
        HERE
        """)
        assert r == const_heredoc("        abc\n")

        r = space.parse("""
        <<-HERE
        #{false}
        HERE
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.DynamicString([
                ast.ConstantString("        "),
                ast.Block([ast.Statement(ast.ConstantBool(False))]),
                ast.ConstantString("\n"),
                ast.ConstantString(""),
            ]))
        ]))

        r = space.parse("""
        <<HERE
        abc #{123}
HERE
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.DynamicString([
                ast.ConstantString("        abc "),
                ast.Block([ast.Statement(ast.ConstantInt(123))]),
                ast.ConstantString("\n"),
                ast.ConstantString(""),
            ]))
        ]))

        r = space.parse("""
        f(<<-HERE, 3)
        abc
        HERE
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(2), "f", [
                ast.ConstantString("        abc\n"),
                ast.ConstantInt(3),
            ], None, 2))
        ]))

    def test_class(self, space):
        r = space.parse("""
        class X
        end""")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Class(ast.Scope(2), "X", None, ast.Nil()))
        ]))

        r = space.parse("""
        class
        X
        end""")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Class(ast.Scope(3), "X", None, ast.Nil()))
        ]))

        r = space.parse("""
        class X
            def f()
                2
            end
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Class(ast.Scope(2), "X", None, ast.Block([
                ast.Statement(ast.Function(3, None, "f", [], None, [], [], None, None, ast.Block([
                    ast.Statement(ast.ConstantInt(2))
                ])))
            ])))
        ]))

        assert space.parse("class X < Object; end") == ast.Main(ast.Block([
            ast.Statement(ast.Class(ast.Scope(1), "X", ast.Constant("Object", 1), ast.Nil()))
        ]))

        assert space.parse("class X < Module::Object; end") == ast.Main(ast.Block([
            ast.Statement(ast.Class(ast.Scope(1), "X", ast.LookupConstant(ast.Constant("Module", 1), "Object", 1), ast.Nil()))
        ]))

        r = space.parse("""
        class X < Object; end

        def f
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Class(ast.Scope(2), "X", ast.Constant("Object", 2), ast.Nil())),
            ast.Statement(ast.Function(4, None, "f", [], None, [], [], None, None, ast.Nil())),
        ]))

    def test_nest_class(self, space):
        r = space.parse("""
        class Foo::Bar
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Class(ast.Constant("Foo", 2), "Bar", None, ast.Nil()))
        ]))

    def test_singleton_class(self, space):
        r = space.parse("class << self; end")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.SingletonClass(ast.Self(1), ast.Nil(), 1))
        ]))

    def test_instance_variable(self, space):
        assert space.parse("@a") == ast.Main(ast.Block([
            ast.Statement(ast.InstanceVariable("@a"))
        ]))
        assert space.parse("@a = 3") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.InstanceVariable("@a"), ast.ConstantInt(3)))
        ]))

    def test_do_block(self, space):
        r = space.parse("""
        x.each do
            puts 1
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(2), "x", [], None, 2), "each", [], ast.SendBlock(2, [], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Send(ast.Self(3), "puts", [ast.ConstantInt(1)], None, 3))
            ])), 2))
        ]))
        r = space.parse("""
        x.each do ||
            puts 1
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(2), "x", [], None, 2), "each", [], ast.SendBlock(2, [], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Send(ast.Self(3), "puts", [ast.ConstantInt(1)], None, 3))
            ])), 2))
        ]))
        r = space.parse("""
        x.each do |a|
            puts a
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(2), "x", [], None, 2), "each", [], ast.SendBlock(2, [ast.Argument("a")], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Send(ast.Self(3), "puts", [ast.Variable("a", 3)], None, 3))
            ])), 2))
        ]))
        r = space.parse("""
        x.meth y.meth do end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(2), "x", [], None, 2), "meth", [ast.Send(ast.Send(ast.Self(2), "y", [], None, 2), "meth", [], None, 2)], ast.SendBlock(2, [], None, [], [], None, None, ast.Nil()), 2))
        ]))
        assert space.parse("each do end") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "each", [], ast.SendBlock(1, [], None, [], [], None, None, ast.Nil()), 1))
        ]))

        r = space.parse("""
        f nil do
        end.foo nil
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(2), "f", [ast.Nil()], ast.SendBlock(2, [], None, [], [], None, None, ast.Nil()), 2), "foo", [ast.Nil()], None, 3))
        ]))

        r = space.parse("""
        run [] do |n|
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(2), "run", [ast.Array([])], ast.SendBlock(2, [ast.Argument("n")], None, [], [], None, None, ast.Nil()), 2))
        ]))

        with self.raises(space, "SyntaxError"):
            space.parse("""
            Mod::Const do end
            """)

    def test_block(self, space):
        assert space.parse("[].map { |x| x }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Array([]), "map", [], ast.SendBlock(1, [ast.Argument("x")], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Variable("x", 1))
            ])), 1))
        ]))
        assert space.parse("[].inject(0) { |x, s| x + s }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Array([]), "inject", [ast.ConstantInt(0)], ast.SendBlock(1, [ast.Argument("x"), ast.Argument("s")], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Send(ast.Variable("x", 1), "+", [ast.Variable("s", 1)], None, 1))
            ])), 1))
        ]))
        assert space.parse("f { 5 }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [], None, [], [], None, None, ast.Block([
                ast.Statement(ast.ConstantInt(5))
            ])), 1))
        ]))
        assert space.parse("f(3) { 5 }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [ast.ConstantInt(3)], ast.SendBlock(1, [], None, [], [], None, None, ast.Block([
                ast.Statement(ast.ConstantInt(5))
            ])), 1))
        ]))
        assert space.parse("f { |*v| v }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [], "v", [], [], None, None, ast.Block([
                ast.Statement(ast.Variable("v", 1))
            ])), 1))
        ]))
        assert space.parse("f (:a) { |b| 1 }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [ast.ConstantSymbol("a")], ast.SendBlock(1, [ast.Argument("b")], None, [], [], None, None, ast.Block([
                ast.Statement(ast.ConstantInt(1)),
            ])), 1))
        ]))
        assert space.parse("a.b (:a) { }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(1), "a", [], None, 1), "b", [ast.ConstantSymbol("a")], ast.SendBlock(1, [], None, [], [], None, None, ast.Nil()), 1))
        ]))
        assert space.parse("f { |a,| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [ast.Argument("a")], "*", [], [], None, None, ast.Nil()), 1))
        ]))
        assert space.parse("f { |a, *s| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [ast.Argument("a")], "s", [], [], None, None, ast.Nil()), 1))
        ]))
        assert space.parse("f { |&s| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [], None, [], [], None, "s", ast.Nil()), 1))
        ]))
        assert space.parse("f { |b=1| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [ast.Argument("b", ast.ConstantInt(1))], None, [], [], None, None, ast.Nil()), 1))
        ]))
        assert space.parse("f { |b=1, &s| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [ast.Argument("b", ast.ConstantInt(1))], None, [], [], None, "s", ast.Nil()), 1))
        ]))
        assert space.parse("f { |x, b=1| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [ast.Argument("x"), ast.Argument("b", ast.ConstantInt(1))], None, [], [], None, None, ast.Nil()), 1))
        ]))
        assert space.parse("f { |x, b=1, &s| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [ast.Argument("x"), ast.Argument("b", ast.ConstantInt(1))], None, [], [], None, "s", ast.Nil()), 1))
        ]))
        assert space.parse("f { |x, b=1, *a, &s| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1, [ast.Argument("x"), ast.Argument("b", ast.ConstantInt(1))], "a", [], [], None, "s", ast.Nil()), 1))
        ]))
        assert space.parse("f { |opt1=1, opt2=2| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1,
                [
                    ast.Argument("opt1", ast.ConstantInt(1)),
                    ast.Argument("opt2", ast.ConstantInt(2))
                ],
                None,
                [], [], None,
                None,
                ast.Nil()
            ), 1))
        ]))
        assert space.parse("f { |opt1=1, *rest, &blk| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1,
                [ast.Argument("opt1", ast.ConstantInt(1))],
                "rest",
                [], [], None,
                "blk",
                ast.Nil()
            ), 1))
        ]))
        assert space.parse("f { |a, (x, y)| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1,
                [
                    ast.Argument("a"),
                    ast.Argument("1"),
                ],
                None, [], [], None, None,
                ast.Block([ast.Statement(
                    ast.MultiAssignment(
                        ast.MultiAssignable([
                            ast.Variable("x", -1),
                            ast.Variable("y", -1),
                        ]),
                        ast.Variable("1", 1)
                    )
                )])
            ), 1)),
        ]))
        assert space.parse("f { |a, (x, (*, y, z)), d, *r, &b| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1,
                [
                    ast.Argument("a"),
                    ast.Argument("1"),
                    ast.Argument("d")
                ],
                "r",
                [], [], None,
                "b",
                ast.Block([ast.Statement(
                    ast.MultiAssignment(
                        ast.MultiAssignable([
                            ast.Variable("x", -1),
                            ast.MultiAssignable([
                                ast.Splat(None),
                                ast.Variable("y", -1),
                                ast.Variable("z", -1)
                            ])
                        ]),
                        ast.Variable("1", 1)
                    )
                )])
            ), 1)),
        ]))
        assert space.parse("f { |(x, y)| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1,
                [ast.Argument("0")],
                None,
                [], [], None,
                None,
                ast.Block([
                    ast.Statement(ast.MultiAssignment(
                        ast.MultiAssignable([
                            ast.Variable("x", -1),
                            ast.Variable("y", -1),
                        ]),
                        ast.Variable("0", 1),
                    ))
                ]),
            ), 1))
        ]))
        assert space.parse("f { |;x, y| }") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.SendBlock(1,
                [], None, [], [], None, None, ast.Nil(),
            ), 1))
        ]))

    def test_lambda(self, space):
        assert space.parse("->{}") == ast.Main(ast.Block([
            ast.Statement(ast.Lambda(ast.SendBlock(1, [], None, [], [], None, None, ast.Nil())))
        ]))

    def test_parens_call(self, space):
        assert space.parse("blk.(1, 2)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Send(ast.Self(1), "blk", [], None, 1),
                "call",
                [ast.ConstantInt(1), ast.ConstantInt(2)],
                None,
                1
            ))
        ]))
        assert space.parse("blk::(1, 2)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(
                ast.Send(ast.Self(1), "blk", [], None, 1),
                "call",
                [ast.ConstantInt(1), ast.ConstantInt(2)],
                None,
                1
            ))
        ]))

    def test_yield(self, space):
        assert space.parse("yield") == ast.Main(ast.Block([
            ast.Statement(ast.Yield([], 1))
        ]))
        assert space.parse("yield 3, 4") == ast.Main(ast.Block([
            ast.Statement(ast.Yield([ast.ConstantInt(3), ast.ConstantInt(4)], 1))
        ]))
        assert space.parse("yield 4") == ast.Main(ast.Block([
            ast.Statement(ast.Yield([ast.ConstantInt(4)], 1))
        ]))
        assert space.parse("yield(*5)") == ast.Main(ast.Block([
            ast.Statement(ast.Yield([ast.Splat(ast.ConstantInt(5))], 1))
        ]))
        assert space.parse("yield()") == ast.Main(ast.Block([
            ast.Statement(ast.Yield([], 1))
        ]))

    def test_symbol(self, space):
        sym = lambda s: ast.Main(ast.Block([
            ast.Statement(ast.ConstantSymbol(s))
        ]))
        assert space.parse(":abc") == sym("abc")
        assert space.parse(":'abc'") == sym("abc")
        assert space.parse(":abc_abc") == sym("abc_abc")
        assert space.parse(":@abc") == sym("@abc")
        assert space.parse(":@@abc") == sym("@@abc")
        assert space.parse(":$abc") == sym("$abc")
        assert space.parse(':"@abc"') == sym("@abc")
        assert space.parse(':""') == sym("")
        assert space.parse(':"#{2}"') == ast.Main(ast.Block([
            ast.Statement(ast.Symbol(ast.DynamicString([ast.Block([ast.Statement(ast.ConstantInt(2))])]), 1))
        ]))
        assert space.parse("%s{foo bar}") == sym("foo bar")
        assert space.parse(":-@") == sym("-@")
        assert space.parse(":+@") == sym("+@")
        assert space.parse(":$-w") == sym("$-w")
        assert space.parse(u":åäö".encode("utf-8")) == sym(u"åäö".encode("utf-8"))
        assert space.parse(u":８ ９ ＡＢＣ".encode("utf-8")) == sym(u"８ ９ ＡＢＣ".encode("utf-8"))

    def test_do_symbol(self, space):
        r = space.parse("f :do")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [ast.ConstantSymbol("do")], None, 1)),
        ]))

    def test_range(self, space):
        assert space.parse("2..3") == ast.Main(ast.Block([
            ast.Statement(ast.Range(ast.ConstantInt(2), ast.ConstantInt(3), False))
        ]))
        assert space.parse("2...3") == ast.Main(ast.Block([
            ast.Statement(ast.Range(ast.ConstantInt(2), ast.ConstantInt(3), True))
        ]))
        assert space.parse("'abc'..'def'") == ast.Main(ast.Block([
            ast.Statement(ast.Range(ast.ConstantString("abc"), ast.ConstantString("def"), False))
        ]))
        assert space.parse("1..-1") == ast.Main(ast.Block([
            ast.Statement(ast.Range(ast.ConstantInt(1), ast.ConstantInt(-1), False))
        ]))

    def test_assign_method(self, space):
        assert space.parse("self.attribute = 3") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Send(ast.Self(1), "attribute", [], None, 1), ast.ConstantInt(3)))
        ]))

        assert space.parse("self.attribute.other_attr.other = 12") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Send(ast.Send(ast.Send(ast.Self(1), "attribute", [], None, 1), "other_attr", [], None, 1), "other", [], None, 1), ast.ConstantInt(12)))
        ]))

    def test_augmented_assignment(self, space):
        assert space.parse("i += 1") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("+", ast.Variable("i", 1), ast.ConstantInt(1)))
        ]))
        assert space.parse("i -= 1") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("-", ast.Variable("i", 1), ast.ConstantInt(1)))
        ]))
        assert space.parse("i *= 5") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("*", ast.Variable("i", 1), ast.ConstantInt(5)))
        ]))

        assert space.parse("self.x += 2") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("+", ast.Send(ast.Self(1), "x", [], None, 1), ast.ConstantInt(2)))
        ]))

        assert space.parse("@a += 3") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("+", ast.InstanceVariable("@a"), ast.ConstantInt(3)))
        ]))

        assert space.parse("self[1] += 2") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("+", ast.Subscript(ast.Self(1), [ast.ConstantInt(1)], 1), ast.ConstantInt(2)))
        ]))

        assert space.parse("x /= 2") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("/", ast.Variable("x", 1), ast.ConstantInt(2)))
        ]))

        assert space.parse("x %= 2") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("%", ast.Variable("x", 1), ast.ConstantInt(2)))
        ]))

        assert space.parse("x |= 2") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("|", ast.Variable("x", 1), ast.ConstantInt(2)))
        ]))

        assert space.parse("x &= 2") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("&", ast.Variable("x", 1), ast.ConstantInt(2)))
        ]))

        assert space.parse("x += f 2") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("+", ast.Variable("x", 1), ast.Send(ast.Self(1), "f", [ast.ConstantInt(2)], None, 1)))
        ]))

        assert space.parse("x ^= 3") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("^", ast.Variable("x", 1), ast.ConstantInt(3)))
        ]))

        assert space.parse("x <<= 3") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("<<", ast.Variable("x", 1), ast.ConstantInt(3)))
        ]))

        assert space.parse("x >>= 3") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment(">>", ast.Variable("x", 1), ast.ConstantInt(3)))
        ]))

        assert space.parse("@a += []") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("+", ast.InstanceVariable("@a"), ast.Array([])))
        ]))

    def test_block_result(self, space):
        r = space.parse("""
        [].inject(0) do |s, x|
            s + x
        end * 5
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Array([]), "inject", [ast.ConstantInt(0)], ast.SendBlock(2, [ast.Argument("s"), ast.Argument("x")], None, [], [], None, None, ast.Block([
                ast.Statement(ast.Send(ast.Variable("s", 3), "+", [ast.Variable("x", 3)], None, 3))
            ])), 2), "*", [ast.ConstantInt(5)], None, 4))
        ]))

    def test_unary_neg(self, space):
        assert space.parse("-b") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(1), "b", [], None, 1), "-@", [], None, 1))
        ]))
        assert space.parse("Math.exp(-a)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Constant("Math", 1), "exp", [ast.Send(ast.Send(ast.Self(1), "a", [], None, 1), "-@", [], None, 1)], None, 1))
        ]))

    def test_unary_ops(self, space):
        assert space.parse("-yield") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Yield([], 1), "-@", [], None, 1))
        ]))
        assert space.parse("~3") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(3), "~", [], None, 1))
        ]))

    def test_unary_pos(self, space):
        assert space.parse("+100") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(100))
        ]))
        assert space.parse("+yield") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Yield([], 1), "+@", [], None, 1))
        ]))

    def test_unless(self, space):
        r = space.parse("""
        unless 1 == 2 then
            return 4
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.Send(ast.ConstantInt(1), "==", [ast.ConstantInt(2)], None, 2), ast.Nil(), ast.Block([
                ast.Return(ast.ConstantInt(4))
            ])))
        ]))

        r = space.parse("""
        unless 0
            5
        else
            7
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(0),
                ast.Block([ast.Statement(ast.ConstantInt(7))]),
                ast.Block([ast.Statement(ast.ConstantInt(5))]),
            ))
        ]))

    def test_constant_lookup(self, space):
        assert space.parse("Module::Constant") == ast.Main(ast.Block([
            ast.Statement(ast.LookupConstant(ast.Constant("Module", 1), "Constant", 1))
        ]))
        assert space.parse("X::m nil") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Constant("X", 1), "m", [ast.Nil()], None, 1))
        ]))
        assert space.parse("::Const") == ast.Main(ast.Block([
            ast.Statement(ast.LookupConstant(None, "Const", 1))
        ]))
        assert space.parse("abc::Constant = 5") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.LookupConstant(ast.Send(ast.Self(1), "abc", [], None, 1), "Constant", 1), ast.ConstantInt(5)))
        ]))

    def test_constant_assignment(self, space):
        assert space.parse("::Const = 5") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.LookupConstant(None, "Const", 1), ast.ConstantInt(5)))
        ]))

    def test___FILE__(self, space):
        assert space.parse("__FILE__") == ast.Main(ast.Block([
            ast.Statement(ast.File())
        ]))
        with self.raises(space, "SyntaxError"):
            space.parse("__FILE__ = 5")

    def test___LINE__(self, space):
        with self.raises(space, "SyntaxError"):
            space.parse("__LINE__ = 2")

    def test_function_default_arguments(self, space):
        function = lambda name, args, pargs: ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, name, args, None, pargs, [], None, None, ast.Nil()))
        ]))

        r = space.parse("""
        def f(a, b=3)
        end
        """)
        assert r == function("f", [ast.Argument("a"), ast.Argument("b", ast.ConstantInt(3))], [])

        r = space.parse("""
        def f(a, b, c=b)
        end
        """)
        assert r == function("f", [ast.Argument("a"), ast.Argument("b"), ast.Argument("c", ast.Variable("b", 2))], [])

        r = space.parse("""
        def f(a=3, b)
        end
        """)
        assert r == function("f", [ast.Argument("a", ast.ConstantInt(3))], [ast.Argument("b")])

        r = space.parse("""
        def f(a, b=3, c)
        end
        """)
        assert r == function("f", [ast.Argument("a"), ast.Argument("b", ast.ConstantInt(3))], [ast.Argument("c")])

        r = space.parse("""
        def f(a=1, b=2)
        end
        """)
        assert r == function("f", [ast.Argument("a", ast.ConstantInt(1)), ast.Argument("b", ast.ConstantInt(2))], [])

        with self.raises(space, "SyntaxError"):
            space.parse("""
            def f(a, b=3, c, d=5)
            end
            """)

    def test_exceptions(self, space):
        r = space.parse("""
        begin
            1 + 1
        rescue ZeroDivisionError
            puts 'zero'
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([
                    ast.Statement(ast.Send(ast.ConstantInt(1), "+", [ast.ConstantInt(1)], None, 3))
                ]),
                [
                    ast.ExceptHandler([ast.Constant("ZeroDivisionError", 4)], None, ast.Block([
                        ast.Statement(ast.Send(ast.Self(5), "puts", [ast.ConstantString("zero")], None, 5))
                    ]))
                ],
                ast.Nil()
            ))
        ]))

        r = space.parse("""
        begin
            1 / 0
        rescue ZeroDivisionError => e
            puts e
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([
                    ast.Statement(ast.Send(ast.ConstantInt(1), "/", [ast.ConstantInt(0)], None, 3))
                ]),
                [
                    ast.ExceptHandler([ast.Constant("ZeroDivisionError", 4)], ast.Variable("e", 4), ast.Block([
                        ast.Statement(ast.Send(ast.Self(5), "puts", [ast.Variable("e", 5)], None, 5))
                    ]))
                ],
                ast.Nil()
            ))
        ]))

        r = space.parse("""
        begin
            1 / 0
        rescue ZeroDivisionError => e
            puts e
        rescue NoMethodError
            puts '?'
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([
                    ast.Statement(ast.Send(ast.ConstantInt(1), "/", [ast.ConstantInt(0)], None, 3))
                ]),
                [
                    ast.ExceptHandler([ast.Constant("ZeroDivisionError", 4)], ast.Variable("e", 4), ast.Block([
                        ast.Statement(ast.Send(ast.Self(5), "puts", [ast.Variable("e", 5)], None, 5))
                    ])),
                    ast.ExceptHandler([ast.Constant("NoMethodError", 6)], None, ast.Block([
                        ast.Statement(ast.Send(ast.Self(7), "puts", [ast.ConstantString("?")], None, 7))
                    ])),
                ],
                ast.Nil()
            ))
        ]))

        r = space.parse("""
        begin
            1 / 0
        rescue
            5
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([
                    ast.Statement(ast.Send(ast.ConstantInt(1), "/", [ast.ConstantInt(0)], None, 3))
                ]),
                [
                    ast.ExceptHandler([], None, ast.Block([
                        ast.Statement(ast.ConstantInt(5))
                    ]))
                ],
                ast.Nil(),
            ))
        ]))

        r = space.parse("""
        begin
            1 / 0
        ensure
            puts 'ensure'
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryFinally(
                ast.Block([
                    ast.Statement(ast.Send(ast.ConstantInt(1), "/", [ast.ConstantInt(0)], None, 3))
                ]),
                ast.Block([
                    ast.Statement(ast.Send(ast.Self(5), "puts", [ast.ConstantString("ensure")], None, 5))
                ]),
            ))
        ]))

        r = space.parse("""
        begin
            1 / 0
        rescue ZeroDivisionError
            puts 'rescue'
        ensure
            puts 'ensure'
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryFinally(
                ast.TryExcept(
                    ast.Block([
                        ast.Statement(ast.Send(ast.ConstantInt(1), "/", [ast.ConstantInt(0)], None, 3))
                    ]),
                    [
                        ast.ExceptHandler([ast.Constant("ZeroDivisionError", 4)], None, ast.Block([
                            ast.Statement(ast.Send(ast.Self(5), "puts", [ast.ConstantString("rescue")], None, 5)),
                        ])),
                    ],
                    ast.Nil()
                ),
                ast.Block([
                    ast.Statement(ast.Send(ast.Self(7), "puts", [ast.ConstantString("ensure")], None, 7))
                ])
            ))
        ]))

        r = space.parse("""
        begin
            1 + 1
            1 / 0
        rescue
            puts 'rescue'
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([
                    ast.Statement(ast.Send(ast.ConstantInt(1), "+", [ast.ConstantInt(1)], None, 3)),
                    ast.Statement(ast.Send(ast.ConstantInt(1), "/", [ast.ConstantInt(0)], None, 4)),
                ]), [
                    ast.ExceptHandler([], None, ast.Block([
                        ast.Statement(ast.Send(ast.Self(6), "puts", [ast.ConstantString("rescue")], None, 6))
                    ]))
                ],
                ast.Nil(),
            ))
        ]))
        r = space.parse("""
        begin
            2
        else
            10
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([ast.Statement(ast.ConstantInt(2))]),
                [],
                ast.Block([ast.Statement(ast.ConstantInt(10))])
            ))
        ]))

        r = space.parse("""
        begin
            2
        rescue E1, E2
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([ast.Statement(ast.ConstantInt(2))]),
                [
                    ast.ExceptHandler([ast.Constant("E1", 4), ast.Constant("E2", 4)], None, ast.Nil()),
                ],
                ast.Nil(),
            ))
        ]))

        r = space.parse("""
        begin
        rescue Mod::Exc
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Nil(),
                [
                    ast.ExceptHandler(
                        [ast.LookupConstant(ast.Constant("Mod", 3), "Exc", 3)],
                        None,
                        ast.Nil(),
                    )
                ],
                ast.Nil(),
            ))
        ]))

    def test_def_exceptions(self, space):
        r = space.parse("""
        def f
            3
        rescue Exception => e
            5
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [], None, [], [], None, None, ast.TryExcept(
                ast.Block([ast.Statement(ast.ConstantInt(3))]),
                [
                    ast.ExceptHandler([ast.Constant("Exception", 4)], ast.Variable("e", 4), ast.Block([
                        ast.Statement(ast.ConstantInt(5))
                    ]))
                ],
                ast.Nil(),
            )))
        ]))

        r = space.parse("""
        def f
            10
        ensure
            5
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [], None, [], [], None, None, ast.TryFinally(
                ast.Block([ast.Statement(ast.ConstantInt(10))]),
                ast.Block([ast.Statement(ast.ConstantInt(5))]),
            )))
        ]))

    def test_begin(self, space):
        r = space.parse("""
        begin
            3
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Block([ast.Statement(ast.ConstantInt(3))]))
        ]))

    def test_module(self, space):
        r = space.parse("""
        module M
            def method
            end
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Module(ast.Scope(2), "M", ast.Block([
                ast.Statement(ast.Function(3, None, "method", [], None, [], [], None, None, ast.Nil()))
            ])))
        ]))

    def test_root_scope_module(self, space):
        r = space.parse("""
        module ::M
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Module(None, "M", ast.Nil()))
        ]))

    def test_question_mark(self, space):
        assert space.parse("obj.method?") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(1), "obj", [], None, 1), "method?", [], None, 1))
        ]))
        assert space.parse("def method?() end") == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "method?", [], None, [], [], None, None, ast.Nil()))
        ]))
        assert space.parse("method?") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "method?", [], None, 1))
        ]))
        with self.raises(space, "SyntaxError"):
            space.parse("method? = 4")

    def test_exclamation_point(self, space):
        assert space.parse("obj.method!") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(1), "obj", [], None, 1), "method!", [], None, 1))
        ]))
        assert space.parse("def method!() end") == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "method!", [], None, [], [], None, None, ast.Nil()))
        ]))
        assert space.parse("method!") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "method!", [], None, 1))
        ]))
        with self.raises(space, "SyntaxError"):
            space.parse("method! = 4")

    def test_singleton_method(self, space):
        r = space.parse("""
        def Array.hello
            'hello world'
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, ast.Constant("Array", 2), "hello", [], None, [], [], None, None, ast.Block([
                ast.Statement(ast.ConstantString("hello world")),
            ])))
        ]))
        r = space.parse("""
        def x.r=
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, ast.Send(ast.Self(2), "x", [], None, 2), "r=", [], None, [], [], None, None, ast.Nil()))
        ]))

    def test_global_var(self, space):
        r = space.parse("""
        $abc_123 = 3
        $abc
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Global("$abc_123"), ast.ConstantInt(3))),
            ast.Statement(ast.Global("$abc")),
        ]))
        simple_global = lambda s: ast.Main(ast.Block([
            ast.Statement(ast.Global(s))
        ]))
        assert space.parse("$>") == simple_global("$>")
        assert space.parse("$:") == simple_global("$:")
        assert space.parse("$$") == simple_global("$$")
        assert space.parse("$?") == simple_global("$?")
        assert space.parse("$\\") == simple_global("$\\")
        assert space.parse("$!") == simple_global("$!")
        assert space.parse('$"') == simple_global('$"')
        assert space.parse("$~") == simple_global("$~")
        assert space.parse("$&") == simple_global("$&")
        assert space.parse("$`") == simple_global("$`")
        assert space.parse("$'") == simple_global("$'")
        assert space.parse("$+") == simple_global("$+")
        assert space.parse("$,") == simple_global("$,")
        assert space.parse("$-w") == simple_global("$-w")
        assert space.parse("$@") == simple_global("$@")
        assert space.parse("$;") == simple_global("$;")
        assert space.parse("$<") == simple_global("$<")
        assert space.parse("$.") == simple_global("$.")

    def test_comments(self, space):
        r = space.parse("""
        #abc 123
        1 + 1 # more comment
        # another comment
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "+", [ast.ConstantInt(1)], None, 3))
        ]))

    def test_send_block_argument(self, space):
        r = space.parse("f(&b)")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [], ast.BlockArgument(ast.Send(ast.Self(1), "b", [], None, 1)), 1))
        ]))

        r = space.parse("f(3, 4, &a)")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [ast.ConstantInt(3), ast.ConstantInt(4)], ast.BlockArgument(ast.Send(ast.Self(1), "a", [], None, 1)), 1))
        ]))

        with self.raises(space, "SyntaxError"):
            space.parse("f(&b, &b)")

        with self.raises(space, "SyntaxError"):
            space.parse("f(&b, a)")

        with self.raises(space, "SyntaxError"):
            space.parse("f(&b) {}")

        with self.raises(space, "SyntaxError"):
            space.parse("""
            f(&b) do ||
            end
            """)

    def test_declare_splat_argument(self, space):
        r = space.parse("def f(*args) end")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "f", [], "args", [], [], None, None, ast.Nil()))
        ]))

        r = space.parse("def f(*args, &g) end")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "f", [], "args", [], [], None, "g", ast.Nil()))
        ]))

        r = space.parse("def f(a, *) end")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(1, None, "f", [ast.Argument("a")], "*", [], [], None, None, ast.Nil()))
        ]))

        with self.raises(space, "SyntaxError"):
            space.parse("def f(*args, g=5)")

    def test_regexp(self, space):
        re = lambda re: ast.Main(ast.Block([
            ast.Statement(ast.ConstantRegexp(re, 0, 1))
        ]))
        dyn_re = lambda re: ast.Main(ast.Block([
            ast.Statement(ast.DynamicRegexp(re, 0))
        ]))
        assert space.parse("//") == re("")
        assert space.parse(r"/a/") == re("a")
        assert space.parse(r"/\w/") == re(r"\w")
        assert space.parse('%r{2}') == re("2")
        assert space.parse('%r{#{2}}') == dyn_re(ast.DynamicString([ast.Block([ast.Statement(ast.ConstantInt(2))])]))
        assert space.parse('/#{2}/') == dyn_re(ast.DynamicString([ast.Block([ast.Statement(ast.ConstantInt(2))])]))
        assert space.parse("%r!a!") == re("a")

    def test_regexp_flags(self, space):
        re = lambda re, flags: ast.Main(ast.Block([
            ast.Statement(ast.ConstantRegexp(re, flags, 1))
        ]))
        assert space.parse('/a/o') == re('a', regexp.ONCE)

    def test_unclosed_regexp(self, space):
        with self.raises(space, "SyntaxError"):
            space.parse("%r{abc")

    def test_or(self, space):
        assert space.parse("3 || 4") == ast.Main(ast.Block([
            ast.Statement(ast.Or(ast.ConstantInt(3), ast.ConstantInt(4)))
        ]))
        assert space.parse("3 + 4 || 4 * 5") == ast.Main(ast.Block([
            ast.Statement(ast.Or(
                ast.Send(ast.ConstantInt(3), "+", [ast.ConstantInt(4)], None, 1),
                ast.Send(ast.ConstantInt(4), "*", [ast.ConstantInt(5)], None, 1),
            ))
        ]))

    def test_and(self, space):
        assert space.parse("3 && 4") == ast.Main(ast.Block([
            ast.Statement(ast.And(ast.ConstantInt(3), ast.ConstantInt(4)))
        ]))
        assert space.parse("4 || 5 && 6") == ast.Main(ast.Block([
            ast.Statement(ast.Or(
                ast.ConstantInt(4),
                ast.And(ast.ConstantInt(5), ast.ConstantInt(6))
            ))
        ]))

    def test_not(self, space):
        assert space.parse("!3") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(3), "!", [], None, 1))
        ]))
        assert space.parse("not 3") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(3), "!", [], None, 1))
        ]))
        assert space.parse("f not(3)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "f", [ast.Send(ast.ConstantInt(3), "!", [], None, 1)], None, 1))
        ]))
        assert space.parse("not()") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Nil(), "!", [], None, 1))
        ]))

    def test_inline_if(self, space):
        assert space.parse("return 5 if 3") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3), ast.Block([
                ast.Return(ast.ConstantInt(5))
            ]), ast.Nil()))
        ]))

    def test_inline_unless(self, space):
        assert space.parse("return 5 unless 3") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3),
                ast.Nil(),
                ast.Block([ast.Return(ast.ConstantInt(5))]),
            ))
        ]))

    def test_inline_until(self, space):
        assert space.parse("i += 1 until 3") == ast.Main(ast.Block([
            ast.Statement(ast.Until(ast.ConstantInt(3), ast.Block([
                ast.Statement(ast.AugmentedAssignment("+", ast.Variable("i", 1), ast.ConstantInt(1)))
            ])))
        ]))

    def test_inline_while(self, space):
        assert space.parse("i += 1 while 3") == ast.Main(ast.Block([
            ast.Statement(ast.While(ast.ConstantInt(3), ast.Block([
                ast.Statement(ast.AugmentedAssignment("+", ast.Variable("i", 1), ast.ConstantInt(1)))
            ])))
        ]))

    def test_inline_rescue(self, space):
        assert space.parse("foo rescue bar") == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([ast.Statement(ast.Send(ast.Self(1), "foo", [], None, 1))]),
                [
                    ast.ExceptHandler([ast.LookupConstant(ast.Scope(1), "StandardError", 1)], None, ast.Block([
                        ast.Statement(ast.Send(ast.Self(1), "bar", [], None, 1))
                    ]))
                ],
                ast.Nil(),
            ))
        ]))
        assert space.parse("a = 2 rescue 3") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("a", 1), ast.TryExcept(
                ast.ConstantInt(2),
                [
                    ast.ExceptHandler([ast.LookupConstant(ast.Scope(1), "StandardError", 1)], None, ast.ConstantInt(3))
                ],
                ast.Nil(),
            )))
        ]))
        assert space.parse("a += 2 rescue 3") == ast.Main(ast.Block([
            ast.Statement(ast.AugmentedAssignment("+", ast.Variable("a", 1), ast.TryExcept(
                ast.ConstantInt(2),
                [
                    ast.ExceptHandler([ast.LookupConstant(ast.Scope(1), "StandardError", 1)], None, ast.ConstantInt(3))
                ],
                ast.Nil(),
            )))
        ]))

    def test_inline_precedence(self, space):
        assert space.parse("return unless x = 3") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.Assignment(ast.Variable("x", 1), ast.ConstantInt(3)),
                ast.Nil(),
                ast.Block([
                    ast.Return(ast.Nil()),
                ])
            ))
        ]))
        r = space.parse("""
        def f
            return unless x = 3
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [], None, [], [], None, None, ast.Block([
                ast.Statement(ast.If(ast.Assignment(ast.Variable("x", 3), ast.ConstantInt(3)),
                    ast.Nil(),
                    ast.Block([
                        ast.Return(ast.Nil())
                    ])
                ))
            ])))
        ]))

    def test_ternary_operator(self, space):
        assert space.parse("3 ? 2 : 5") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3),
                ast.ConstantInt(2),
                ast.ConstantInt(5),
            ))
        ]))
        assert space.parse("0 ? nil : nil") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(0),
                ast.Nil(),
                ast.Nil(),
            ))
        ]))
        assert space.parse("empty? ? '[]' : nil") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.Send(ast.Self(1), "empty?", [], None, 1),
                ast.ConstantString("[]"),
                ast.Nil(),
            ))
        ]))
        assert space.parse("0 ? ?- : ?w") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(0),
                ast.ConstantString("-"),
                ast.ConstantString("w"),
            ))
        ]))
        assert space.parse("0 ? ?T:0") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(0),
                ast.ConstantString("T"),
                ast.ConstantInt(0),
            ))
        ]))
        r = space.parse("""
        (0 ? 0 : '')
        0
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Block([ast.Statement(ast.If(ast.ConstantInt(0),
                ast.ConstantInt(0),
                ast.ConstantString(""),
            ))])),
            ast.Statement(ast.ConstantInt(0)),
        ]))
        assert space.parse("0 ? (0) :(0)") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(0),
                ast.Block([ast.Statement(ast.ConstantInt(0))]),
                ast.Block([ast.Statement(ast.ConstantInt(0))]),
            ))
        ]))
        r = space.parse("""
        0 ? (0) :
                 0
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(0),
                ast.Block([ast.Statement(ast.ConstantInt(0))]),
                ast.ConstantInt(0),
            ))
        ]))
        r = space.parse("""
        0 ?
        (0) : 0
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(0),
                ast.Block([ast.Statement(ast.ConstantInt(0))]),
                ast.ConstantInt(0),
            ))
        ]))

    def test_case(self, space):
        r = space.parse("""
        case 3
        when 5 then
            6
        when 4
            7
        else
            9
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Case(ast.ConstantInt(3), [
                ast.When([ast.ConstantInt(5)], ast.Block([ast.Statement(ast.ConstantInt(6))]), 3),
                ast.When([ast.ConstantInt(4)], ast.Block([ast.Statement(ast.ConstantInt(7))]), 5)
            ], ast.Block([ast.Statement(ast.ConstantInt(9))])))
        ]))
        r = space.parse("""
        case 3
        when 4,5 then
            6
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Case(ast.ConstantInt(3), [
                ast.When([ast.ConstantInt(4), ast.ConstantInt(5)], ast.Block([ast.Statement(ast.ConstantInt(6))]), 3),
            ], ast.Nil()))
        ]))

    def test_case_regexp(self, space):
        r = space.parse("""
        case 0
        when /a/
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Case(ast.ConstantInt(0), [
                ast.When([ast.ConstantRegexp("a", 0, 3)], ast.Nil(), 3)
            ], ast.Nil()))
        ]))

    def test_case_without_expr(self, space):
        r = space.parse("""
        case
        when 3 then
            5
        when 4 == 2
            3
        else
            9
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3), ast.Block([
                ast.Statement(ast.ConstantInt(5))
            ]),
                ast.If(ast.Send(ast.ConstantInt(4), "==", [ast.ConstantInt(2)], None, 5), ast.Block([
                    ast.Statement(ast.ConstantInt(3))
                ]), ast.Block([
                    ast.Statement(ast.ConstantInt(9))
                ]))
            ))
        ]))
        r = space.parse("""
        case
        when 4,5 then
            6
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.Or(ast.ConstantInt(4), ast.ConstantInt(5)), ast.Block([
                ast.Statement(ast.ConstantInt(6))
            ]), ast.Nil()))
        ]))
        r = space.parse("""
        case
        when 4
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(4), ast.Nil(), ast.Nil()))
        ]))

    def test_and_regexp(self, space):
        assert space.parse("3 && /a/") == ast.Main(ast.Block([
            ast.Statement(ast.And(ast.ConstantInt(3), ast.ConstantRegexp("a", 0, 1)))
        ]))

    def test_hash(self, space):
        assert space.parse("{}") == ast.Main(ast.Block([
            ast.Statement(ast.Hash([]))
        ]))
        assert space.parse("{:abc => 3, :def => 5}") == ast.Main(ast.Block([
            ast.Statement(ast.Hash([
                (ast.ConstantSymbol("abc"), ast.ConstantInt(3)),
                (ast.ConstantSymbol("def"), ast.ConstantInt(5)),
            ]))
        ]))
        r = space.parse("""
        {
            :k => :v
        }
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Hash([
                (ast.ConstantSymbol("k"), ast.ConstantSymbol("v")),
            ]))
        ]))
        assert space.parse("{a = 2 => 3, yield => 5}") == ast.Main(ast.Block([
            ast.Statement(ast.Hash([
                (ast.Assignment(ast.Variable("a", 1), ast.ConstantInt(2)), ast.ConstantInt(3)),
                (ast.Yield([], 1), ast.ConstantInt(5))
            ]))
        ]))
        r = space.parse("""
        x ||= {
        }
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.OrEqual(ast.Variable("x", 2), ast.Hash([])))
        ]))
        assert space.parse("{begin: 1, end: 2, self: 3, nil: 4, true: 5, false: 6}") == ast.Main(ast.Block([
            ast.Statement(ast.Hash([
                (ast.ConstantSymbol("begin"), ast.ConstantInt(1)),
                (ast.ConstantSymbol("end"), ast.ConstantInt(2)),
                (ast.ConstantSymbol("self"), ast.ConstantInt(3)),
                (ast.ConstantSymbol("nil"), ast.ConstantInt(4)),
                (ast.ConstantSymbol("true"), ast.ConstantInt(5)),
                (ast.ConstantSymbol("false"), ast.ConstantInt(6)),
            ]))
        ]))

    def test_new_hash(self, space):
        r = space.parse("{a: 2, :b => 3, c: 4}")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Hash([
                (ast.ConstantSymbol("a"), ast.ConstantInt(2)),
                (ast.ConstantSymbol("b"), ast.ConstantInt(3)),
                (ast.ConstantSymbol("c"), ast.ConstantInt(4)),
            ]))
        ]))

    def test_newline(self, space):
        r = space.parse("""
        x = 123 &&
            456
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.Variable("x", 2), ast.And(ast.ConstantInt(123), ast.ConstantInt(456))))
        ]))

        r = space.parse("""
        f {
        }
        1
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(2), "f", [], ast.SendBlock(2, [], None, [], [], None, None, ast.Nil()), 2)),
            ast.Statement(ast.ConstantInt(1))
        ]))

        r = space.parse("""
        f()\\
            .m()
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(2), "f", [], None, 2), "m", [], None, 3))
        ]))

        r = space.parse("""
        self.f
            .m()
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Self(2), "f", [], None, 2), "m", [], None, 3))
        ]))

    def test_or_equal(self, space):
        r = space.parse("@a ||= 5")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.OrEqual(ast.InstanceVariable("@a"), ast.ConstantInt(5)))
        ]))

    def test_and_equal(self, space):
        r = space.parse("x &&= 10")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.AndEqual(ast.Variable("x", 1), ast.ConstantInt(10)))
        ]))

    def test_class_variables(self, space):
        r = space.parse("""
        @@a = @@b
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Assignment(ast.ClassVariable("@@a", 2), ast.ClassVariable("@@b", 2)))
        ]))

    def test_shellout(self, space):
        shellout = lambda *components: ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(1), "`", list(components), None, 1))
        ]))
        assert space.parse("`ls`") == shellout(ast.ConstantString("ls"))
        assert space.parse('%x(ls)') == shellout(ast.ConstantString("ls"))
        assert space.parse("`#{2}`") == shellout(ast.DynamicString([ast.Block([ast.Statement(ast.ConstantInt(2))])]))
        assert space.parse("%x(#{2})") == shellout(ast.DynamicString([ast.Block([ast.Statement(ast.ConstantInt(2))])]))

    def test_strings(self, space):
        cstr = lambda c: ast.Main(ast.Block([
            ast.Statement(ast.ConstantString(c))
        ]))
        assert space.parse("'a' 'b' 'c'") == cstr("abc")
        assert space.parse("'a' \"b\"") == cstr("ab")
        assert space.parse('"a" "b"') == cstr("ab")
        assert space.parse('"a" \'b\'') == cstr("ab")
        assert space.parse("""
        'a' \\
        'b'
        """) == cstr("ab")
        assert space.parse("%{a} 'b'") == cstr("ab")
        with self.raises(space, "SyntaxError"):
            space.parse("%{a} %{b}")
        with self.raises(space, "SyntaxError"):
            space.parse("%{a} 'b' %{b}")
        with self.raises(space, "SyntaxError"):
            space.parse("'b' %{b}")

    def test_alias(self, space):
        assert space.parse("alias a b") == ast.Main(ast.Block([
            ast.Alias(ast.ConstantSymbol("a"), ast.ConstantSymbol("b"), 1)
        ]))
        assert space.parse("alias << b") == ast.Main(ast.Block([
            ast.Alias(ast.ConstantSymbol("<<"), ast.ConstantSymbol("b"), 1)
        ]))
        assert space.parse("alias :a :b") == ast.Main(ast.Block([
            ast.Alias(ast.ConstantSymbol("a"), ast.ConstantSymbol("b"), 1)
        ]))

    def test_defined(self, space):
        assert space.parse("defined? Const") == ast.Main(ast.Block([
            ast.Statement(ast.Defined(ast.Constant("Const", 1), 1))
        ]))
        assert space.parse("defined?(3)") == ast.Main(ast.Block([
            ast.Statement(ast.Defined(ast.ConstantInt(3), 1))
        ]))

    def test_super(self, space):
        assert space.parse("super") == ast.Main(ast.Block([
            ast.Statement(ast.Super([], None, 1))
        ]))
        assert space.parse("super(nil)") == ast.Main(ast.Block([
            ast.Statement(ast.Super([ast.Nil()], None, 1))
        ]))
        assert space.parse("super nil") == ast.Main(ast.Block([
            ast.Statement(ast.Super([ast.Nil()], None, 1))
        ]))
        assert space.parse("super()") == ast.Main(ast.Block([
            ast.Statement(ast.Super([], None, 1))
        ]))

    def test_next(self, space):
        assert space.parse("next") == ast.Main(ast.Block([
            ast.Next(ast.Nil())
        ]))
        assert space.parse("next true") == ast.Main(ast.Block([
            ast.Next(ast.ConstantBool(True))
        ]))
        assert space.parse("next 3, 4") == ast.Main(ast.Block([
            ast.Next(ast.Array([ast.ConstantInt(3), ast.ConstantInt(4)]))
        ]))

    def test_break(self, space):
        assert space.parse("break") == ast.Main(ast.Block([
            ast.Break(ast.Nil())
        ]))
        assert space.parse("break true") == ast.Main(ast.Block([
            ast.Break(ast.ConstantBool(True))
        ]))
        assert space.parse("break 3, 4") == ast.Main(ast.Block([
            ast.Break(ast.Array([ast.ConstantInt(3), ast.ConstantInt(4)]))
        ]))

    def test_undef(self, space):
        r = space.parse("""
        class X
            undef to_s
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Class(ast.Scope(2), "X", None, ast.Block([
                ast.Undef([ast.ConstantSymbol("to_s")], 3)
            ])))
        ]))

    def test_custom_lineno(self, space):
        with self.raises(space, "SyntaxError", "line 1 (unexpected Token(LBRACE_ARG, {))"):
            assert space.parse("[]{}[]")
        with self.raises(space, "SyntaxError", "line 10 (unexpected Token(LBRACE_ARG, {))"):
            assert space.parse("[]{}[]", 10)

    def test_lineno(self, space):
        r = space.parse("""
        <<HERE

HERE
        __LINE__
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("\n")),
            ast.Statement(ast.Line(5)),
        ]))

        r = space.parse("""
        %W(hello
           world)
        __LINE__
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Array([ast.ConstantString("hello"), ast.ConstantString("world")])),
            ast.Statement(ast.Line(4)),
        ]))

        r = space.parse("""
        %w(a\\
b)
        __LINE__
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Array([ast.ConstantString("a\nb")])),
            ast.Statement(ast.Line(4)),
        ]))

    def test_multiline_comments(self, space):
        r = space.parse("""
        1 + 1
=begin
foo bar
=end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "+", [ast.ConstantInt(1)], None, 2))
        ]))

        with self.raises(space, 'SyntaxError'):
            space.parse(" =begin\nfoo\n=end")

        with self.raises(space, 'SyntaxError'):
            space.parse("=begin\nfoo\nbar")

        with self.raises(space, 'SyntaxError'):
            space.parse("=foo\nbar\n=end")

        with self.raises(space, 'SyntaxError'):
            space.parse("=begin\nbar\n=foo")

    def test_multiline_comments_lineno(self, space):
        r = space.parse("""
=begin
some
lines
=end
        1 + 1
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(1), "+", [ast.ConstantInt(1)], None, 6))
        ]))

    def test_call_no_space_symbol(self, space):
        r = space.parse("""
        def f
        end

        f:bar
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function(2, None, "f", [], None, [], [], None, None, ast.Nil())),
            ast.Statement(ast.Send(ast.Self(5), "f", [ast.ConstantSymbol("bar")], None, 5))
        ]))
