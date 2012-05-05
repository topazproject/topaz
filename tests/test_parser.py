import py

from rupypy import ast


class TestParser(object):
    def test_int_constant(self, space):
        assert space.parse("1") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(1))
        ]))
        assert space.parse("-1") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantInt(-1))
        ]))

    def test_float(self, space):
        assert space.parse("0.2") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantFloat(0.2))
        ]))

    def test_binary_expression(self, space):
        assert space.parse("1+1") == ast.Main(ast.Block([
            ast.Statement(ast.BinOp("+", ast.ConstantInt(1), ast.ConstantInt(1)))
        ]))
        assert space.parse("1/1") == ast.Main(ast.Block([ast.Statement(
            ast.BinOp("/", ast.ConstantInt(1), ast.ConstantInt(1)))
        ]))

    def test_multi_term_expr(self, space):
        assert space.parse("1 + 2 * 3") == ast.Main(ast.Block([
            ast.Statement(ast.BinOp("+", ast.ConstantInt(1), ast.BinOp("*", ast.ConstantInt(2), ast.ConstantInt(3))))
        ]))
        assert space.parse("1 * 2 + 3") == ast.Main(ast.Block([
            ast.Statement(ast.BinOp("+", ast.BinOp("*", ast.ConstantInt(1), ast.ConstantInt(2)), ast.ConstantInt(3)))
        ]))
        assert space.parse("2 << 3 * 4") == ast.Main(ast.Block([
            ast.Statement(ast.BinOp("<<", ast.ConstantInt(2), ast.BinOp("*", ast.ConstantInt(3), ast.ConstantInt(4))))
        ]))

    def test_parens(self, space):
        assert space.parse("1 * (2 - 3)") == ast.Main(ast.Block([
            ast.Statement(ast.BinOp("*", ast.ConstantInt(1), ast.BinOp("-", ast.ConstantInt(2), ast.ConstantInt(3))))
        ]))

    def test_multiple_statements_no_sep(self, space):
        with py.test.raises(Exception):
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
            ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(2)]))
        ]))
        assert space.parse("puts 1, 2") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(1), ast.ConstantInt(2)
            ]))]))
        assert space.parse("puts(1, 2)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(1), ast.ConstantInt(2)]))
        ]))
        assert space.parse("2.to_s") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", []))
        ]))
        assert space.parse("2.to_s 10") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.ConstantInt(10)]))
        ]))
        assert space.parse("2.to_s.to_i") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.ConstantInt(2), "to_s", []), "to_i", []))
        ]))
        assert space.parse("2.to_s()") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", []))
        ]))
        assert space.parse("2.to_s(10)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantInt(2), "to_s", [ast.ConstantInt(10)]))
        ]))

    def test_assignment(self, space):
        assert space.parse("a = 3") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment("=", "a", ast.ConstantInt(3)))
        ]))
        assert space.parse("a = b = 3") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment("=", "a", ast.Assignment("=", "b", ast.ConstantInt(3))))
        ]))

    def test_load_variable(self, space):
        assert space.parse("a") == ast.Main(ast.Block([
            ast.Statement(ast.Variable("a"))
        ]))

    def test_if_statement(self, space):
        res = ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3), ast.Block([
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(2)]))
            ]), ast.Block([])))
        ]))
        assert space.parse("if 3 then puts 2 end") == res
        assert space.parse("""
        if 3
            puts 2
        end
        """) == res
        assert space.parse("if 3; puts 2 end") == res
        assert space.parse("if 3; end") == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.ConstantInt(3), ast.Block([]), ast.Block([])))
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
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(2)])),
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(3)])),
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(4)])),
            ]), ast.Block([])))
        ]))

    def test_comparison_ops(self, space):
        assert space.parse("1 == 2; 1 < 2; 1 > 2; 1 != 2; 1 <= 2; 1 >= 2") == ast.Main(ast.Block([
            ast.Statement(ast.BinOp("==", ast.ConstantInt(1), ast.ConstantInt(2))),
            ast.Statement(ast.BinOp("<", ast.ConstantInt(1), ast.ConstantInt(2))),
            ast.Statement(ast.BinOp(">", ast.ConstantInt(1), ast.ConstantInt(2))),
            ast.Statement(ast.BinOp("!=", ast.ConstantInt(1), ast.ConstantInt(2))),
            ast.Statement(ast.BinOp("<=", ast.ConstantInt(1), ast.ConstantInt(2))),
            ast.Statement(ast.BinOp(">=", ast.ConstantInt(1), ast.ConstantInt(2))),
        ]))

    def test_while(self, space):
        expected = ast.Main(ast.Block([
            ast.Statement(ast.While(ast.Variable("true"), ast.Block([
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(5)]))
            ])))
        ]))
        assert space.parse("while true do puts 5 end") == expected
        assert space.parse("while true do; puts 5 end") == expected
        assert space.parse("while true; puts 5 end") == expected
        assert space.parse("while true; end") == ast.Main(ast.Block([
            ast.Statement(ast.While(ast.Variable("true"), ast.Block([
                ast.Statement(ast.Variable("nil"))
            ])))
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
            ast.Statement(ast.Assignment("=", "i", ast.ConstantInt(0))),
            ast.Statement(ast.While(ast.BinOp("<", ast.Variable("i"), ast.ConstantInt(10)), ast.Block([
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("i")])),
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(1)])),
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("i")])),
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("true")])),
            ])))
        ]))

    def test_return(self, space):
        assert space.parse("return 4") == ast.Main(ast.Block([
            ast.Return(ast.ConstantInt(4))
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

    def test_subscript(self, space):
        assert space.parse("[1][0]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Array([ast.ConstantInt(1)]), "[]", [ast.ConstantInt(0)]))
        ]))

        assert space.parse("self[i]") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Variable("self"), "[]", [ast.Variable("i")]))
        ]))

        assert space.parse("self[i].to_s") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Send(ast.Variable("self"), "[]", [ast.Variable("i")]), "to_s", []))
        ]))

    def test_def(self, space):
        assert space.parse("def f() end") == ast.Main(ast.Block([
            ast.Statement(ast.Function("f", [], ast.Block([])))
        ]))

        assert space.parse("def f(a, b) a + b end") == ast.Main(ast.Block([
            ast.Statement(ast.Function("f", [ast.Argument("a"), ast.Argument("b")], ast.Block([
                ast.Statement(ast.BinOp("+", ast.Variable("a"), ast.Variable("b")))
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
            ast.Statement(ast.Function("f", [ast.Argument("a")], ast.Block([
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("a")])),
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("a")])),
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("a")])),
            ])))
        ]))

        assert space.parse("x = def f() end") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment("=", "x", ast.Function("f", [], ast.Block([]))))
        ]))

        r = space.parse("""
        def f a, b
            a + b
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Function("f", [ast.Argument("a"), ast.Argument("b")], ast.Block([
                ast.Statement(ast.BinOp("+", ast.Variable("a"), ast.Variable("b")))
            ])))
        ]))

    def test_string(self, space):
        assert space.parse('"abc"') == ast.Main(ast.Block([
            ast.Statement(ast.ConstantString("abc"))
        ]))
        assert space.parse('"abc".size') == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.ConstantString("abc"), "size", []))
        ]))

    def test_class(self, space):
        r = space.parse("""
        class X
        end""")
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Class("X", None, ast.Block([])))
        ]))

        r = space.parse("""
        class X
            def f()
                2
            end
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.Class("X", None, ast.Block([
                ast.Statement(ast.Function("f", [], ast.Block([
                    ast.Statement(ast.ConstantInt(2))
                ])))
            ])))
        ]))

        assert space.parse("class X < Object; end") == ast.Main(ast.Block([
            ast.Statement(ast.Class("X", ast.Variable("Object"), ast.Block([])))
        ]))

    def test_instance_variable(self, space):
        assert space.parse("@a") == ast.Main(ast.Block([
            ast.Statement(ast.InstanceVariable("a"))
        ]))
        assert space.parse("@a = 3") == ast.Main(ast.Block([
            ast.Statement(ast.InstanceVariableAssignment("=", "a", ast.ConstantInt(3)))
        ]))

    def test_do_block(self, space):
        r = space.parse("""
        x.each do
            puts 1
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.SendBlock(ast.Variable("x"), "each", [], [], ast.Block([
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(1)]))
            ])))
        ]))
        r = space.parse("""
        x.each do ||
            puts 1
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.SendBlock(ast.Variable("x"), "each", [], [], ast.Block([
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantInt(1)]))
            ])))
        ]))
        r = space.parse("""
        x.each do |a|
            puts a
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.SendBlock(ast.Variable("x"), "each", [], [ast.Argument("a")], ast.Block([
                ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("a")]))
            ])))
        ]))

    def test_yield(self, space):
        assert space.parse("yield") == ast.Main(ast.Block([
            ast.Statement(ast.Yield([]))
        ]))
        assert space.parse("yield 3, 4") == ast.Main(ast.Block([
            ast.Statement(ast.Yield([ast.ConstantInt(3), ast.ConstantInt(4)]))
        ]))
        assert space.parse("yield 4") == ast.Main(ast.Block([
            ast.Statement(ast.Yield([ast.ConstantInt(4)]))
        ]))

    def test_symbol(self, space):
        assert space.parse(":abc") == ast.Main(ast.Block([
            ast.Statement(ast.ConstantSymbol("abc"))
        ]))

    def test_range(self, space):
        assert space.parse("2..3") == ast.Main(ast.Block([
            ast.Statement(ast.Range(ast.ConstantInt(2), ast.ConstantInt(3), False))
        ]))
        assert space.parse("2...3") == ast.Main(ast.Block([
            ast.Statement(ast.Range(ast.ConstantInt(2), ast.ConstantInt(3), True))
        ]))
        assert space.parse('"abc".."def"') == ast.Main(ast.Block([
            ast.Statement(ast.Range(ast.ConstantString("abc"), ast.ConstantString("def"), False))
        ]))

    def test_assign_method(self, space):
        assert space.parse("self.attribute = 3") == ast.Main(ast.Block([
            ast.Statement(ast.MethodAssignment("=", ast.Variable("self"), "attribute", ast.ConstantInt(3)))
        ]))

        assert space.parse("self.attribute.other_attr.other = 12") == ast.Main(ast.Block([
            ast.Statement(ast.MethodAssignment("=", ast.Send(ast.Send(ast.Variable("self"), "attribute", []), "other_attr", []), "other", ast.ConstantInt(12)))
        ]))

    def test_augmented_assignment(self, space):
        assert space.parse("i += 1") == ast.Main(ast.Block([
            ast.Statement(ast.Assignment("+=", "i", ast.ConstantInt(1)))
        ]))

        assert space.parse("self.x += 2") == ast.Main(ast.Block([
            ast.Statement(ast.MethodAssignment("+=", ast.Variable("self"), "x", ast.ConstantInt(2)))
        ]))

        assert space.parse("@a += 3") == ast.Main(ast.Block([
            ast.Statement(ast.InstanceVariableAssignment("+=", "a", ast.ConstantInt(3)))
        ]))

    def test_block_result(self, space):
        r = space.parse("""
        [].inject(0) do |s, x|
            s + x
        end * 5
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.BinOp("*", ast.SendBlock(ast.Array([]), "inject", [ast.ConstantInt(0)], [ast.Argument("s"), ast.Argument("x")], ast.Block([
                ast.Statement(ast.BinOp("+", ast.Variable("s"), ast.Variable("x")))
            ])), ast.ConstantInt(5)))
        ]))

    def test_unary_neg(self, space):
        assert space.parse("(-b)") == ast.Main(ast.Block([
            ast.Statement(ast.UnaryOp("-", ast.Variable("b")))
        ]))
        assert space.parse("Math.exp(-a)") == ast.Main(ast.Block([
            ast.Statement(ast.Send(ast.Variable("Math"), "exp", [ast.UnaryOp("-", ast.Variable("a"))]))
        ]))

    def test_unless(self, space):
        r = space.parse("""
        unless 1 == 2 then
            return 4
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.If(ast.BinOp("==", ast.ConstantInt(1), ast.ConstantInt(2)), ast.Block([]), ast.Block([
                ast.Return(ast.ConstantInt(4))
            ])))
        ]))

    def test_constant_lookup(self, space):
        assert space.parse("Module::Constant") == ast.Main(ast.Block([
            ast.Statement(ast.LookupConstant(ast.Variable("Module"), "Constant"))
        ]))

    def test___FILE__(self, space):
        assert space.parse("__FILE__") == ast.Main(ast.Block([
            ast.Statement(ast.Variable("__FILE__"))
        ]))
        with py.test.raises(Exception):
            space.parse("__FILE__ = 5")

    def test_function_default_arguments(self, space):
        function = lambda name, args: ast.Main(ast.Block([
            ast.Statement(ast.Function(name, args, ast.Block([])))
        ]))

        r = space.parse("""
        def f(a, b=3)
        end
        """)
        assert r == function("f", [ast.Argument("a"), ast.Argument("b", ast.ConstantInt(3))])

        r = space.parse("""
        def f(a, b, c=b)
        end
        """)
        assert r == function("f", [ast.Argument("a"), ast.Argument("b"), ast.Argument("c", ast.Variable("b"))])

        r = space.parse("""
        def f(a=3, b)
        end
        """)
        assert r == function("f", [ast.Argument("a", ast.ConstantInt(3)), ast.Argument("b")])

        r = space.parse("""
        def f(a, b=3, c)
        end
        """)
        assert r == function("f", [ast.Argument("a"), ast.Argument("b", ast.ConstantInt(3)), ast.Argument("c")])

        with py.test.raises(Exception):
            space.parse("""
            def f(a, b=3, c, d=5)
            end
            """)

    def test_exceptions(self, space):
        r = space.parse("""
        begin
            1 + 1
        rescue ZeroDivisionError
            puts "zero"
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([
                    ast.Statement(ast.BinOp("+", ast.ConstantInt(1), ast.ConstantInt(1)))
                ]),
                [
                    ast.ExceptHandler(ast.Variable("ZeroDivisionError"), None, ast.Block([
                        ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantString("zero")]))
                    ]))
                ]
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
                    ast.Statement(ast.BinOp("/", ast.ConstantInt(1), ast.ConstantInt(0)))
                ]),
                [
                    ast.ExceptHandler(ast.Variable("ZeroDivisionError"), "e", ast.Block([
                        ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("e")]))
                    ]))
                ]
            ))
        ]))

        r = space.parse("""
        begin
            1 / 0
        rescue ZeroDivisionError => e
            puts e
        rescue NoMethodError
            puts "?"
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryExcept(
                ast.Block([
                    ast.Statement(ast.BinOp("/", ast.ConstantInt(1), ast.ConstantInt(0)))
                ]),
                [
                    ast.ExceptHandler(ast.Variable("ZeroDivisionError"), "e", ast.Block([
                        ast.Statement(ast.Send(ast.Self(), "puts", [ast.Variable("e")]))
                    ])),
                    ast.ExceptHandler(ast.Variable("NoMethodError"), None, ast.Block([
                        ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantString("?")]))
                    ])),
                ]
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
                    ast.Statement(ast.BinOp("/", ast.ConstantInt(1), ast.ConstantInt(0)))
                ]),
                [
                    ast.ExceptHandler(None, None, ast.Block([
                        ast.Statement(ast.ConstantInt(5))
                    ]))
                ]
            ))
        ]))

        r = space.parse("""
        begin
            1 / 0
        ensure
            puts "ensure"
        end
        """)
        assert r == ast.Main(ast.Block([
            ast.Statement(ast.TryFinally(
                ast.Block([
                    ast.Statement(ast.BinOp("/", ast.ConstantInt(1), ast.ConstantInt(0)))
                ]),
                ast.Block([
                    ast.Statement(ast.Send(ast.Self(), "puts", [ast.ConstantString("ensure")]))
                ])
            ))
        ]))
