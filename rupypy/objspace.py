from __future__ import absolute_import

import os

from pypy.rlib import jit
from pypy.rlib.objectmodel import specialize
from pypy.rlib.parsing.parsing import ParseError
from pypy.tool.cache import Cache

from rupypy.astcompiler import CompilerContext, SymbolTable
from rupypy.error import RubyError
from rupypy.frame import Frame
from rupypy.globals import Globals
from rupypy.interpreter import Interpreter
from rupypy.lexer import LexerError
from rupypy.lib.random import W_Random
from rupypy.module import ClassCache, ModuleCache
from rupypy.modules.comparable import Comparable
from rupypy.modules.math import Math
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.boolobject import W_TrueObject, W_FalseObject
from rupypy.objects.classobject import W_ClassObject
from rupypy.objects.codeobject import W_CodeObject
from rupypy.objects.fileobject import W_FileObject
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.functionobject import W_UserFunction
from rupypy.objects.exceptionobject import (W_ExceptionObject, W_NoMethodError,
    W_ZeroDivisionError, W_SyntaxError)
from rupypy.objects.hashobject import W_HashObject
from rupypy.objects.intobject import W_IntObject
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.nilobject import W_NilObject
from rupypy.objects.objectobject import W_Object
from rupypy.objects.procobject import W_ProcObject
from rupypy.objects.rangeobject import W_RangeObject
from rupypy.objects.regexpobject import W_RegexpObject
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.symbolobject import W_SymbolObject
from rupypy.parser import Transformer, _parse, ToASTVisitor


class SpaceCache(Cache):
    def __init__(self, space):
        Cache.__init__(self)
        self.space = space

    def _build(self, obj):
        return obj(self.space)


class ObjectSpace(object):
    def __init__(self):
        self.transformer = Transformer()
        self.cache = SpaceCache(self)
        self.globals = Globals()
        self.w_top_self = W_Object(self, self.getclassfor(W_Object))

        self.w_true = W_TrueObject()
        self.w_false = W_FalseObject()
        self.w_nil = W_NilObject()

        for cls in [
            W_Object, W_ArrayObject, W_FileObject, W_NoMethodError,
            W_ZeroDivisionError, W_SyntaxError, W_Random,
        ]:
            self.add_class(cls)

        for module in [Math, Comparable]:
            self.add_module(module)

        w_load_path = self.newarray([
            self.newstr_fromstr(
                os.path.join(os.path.dirname(__file__), os.path.pardir, "lib-ruby")
            )
        ])
        self.globals.set(self, "$LOAD_PATH", w_load_path)
        self.globals.set(self, "$:", w_load_path)

    def _freeze_(self):
        return True

    @specialize.memo()
    def fromcache(self, key):
        return self.cache.getorbuild(key)

    # Setup methods

    def add_module(self, module):
        "NOT_RPYTHON"
        w_cls = self.getclassfor(W_Object)
        w_cls._lazy_set_const(self, module.moduledef.name, module)

    def add_class(self, cls):
        "NOT_RPYTHON"
        w_cls = self.getclassfor(W_Object)
        w_cls._lazy_set_const(self, cls.classdef.name, cls)

    # Methods for dealing with source code.

    def parse(self, ec, source):
        try:
            st = ToASTVisitor().transform(_parse(source))
            return self.transformer.visit_main(st)
        except ParseError as e:
            self.raise_(ec, self.getclassfor(W_SyntaxError), "line %d" % e.source_pos.lineno)
        except LexerError:
            self.raise_(ec, self.getclassfor(W_SyntaxError))

    def compile(self, ec, source, filepath):
        astnode = self.parse(ec, source)
        symtable = SymbolTable()
        astnode.locate_symbols(symtable)
        c = CompilerContext(self, "<main>", symtable, filepath)
        astnode.compile(c)
        return c.create_bytecode([], [], None, None)

    def execute(self, ec, source, w_self=None, w_scope=None, filepath="-e"):
        bc = self.compile(ec, source, filepath)
        frame = self.create_frame(bc, w_self=w_self, w_scope=w_scope)
        with ec.visit_frame(frame):
            return self.execute_frame(ec, frame, bc)

    def create_frame(self, bc, w_self=None, w_scope=None, block=None,
        parent_interp=None):

        if w_self is None:
            w_self = self.w_top_self
        if w_scope is None:
            w_scope = self.getclassfor(W_Object)
        return Frame(jit.promote(bc), w_self, w_scope, block, parent_interp)

    def execute_frame(self, ec, frame, bc):
        return Interpreter().interpret(ec, frame, bc)

    # Methods for allocating new objects.

    def newbool(self, boolvalue):
        if boolvalue:
            return self.w_true
        else:
            return self.w_false

    def newint(self, intvalue):
        return W_IntObject(intvalue)

    def newfloat(self, floatvalue):
        return W_FloatObject(floatvalue)

    def newsymbol(self, symbol):
        return W_SymbolObject(symbol)

    def newstr_fromchars(self, chars):
        return W_StringObject.newstr_fromchars(self, chars)

    def newstr_fromstr(self, strvalue):
        return W_StringObject.newstr_fromstr(self, strvalue)

    def newarray(self, items_w):
        return W_ArrayObject(items_w)

    def newhash(self):
        return W_HashObject()

    def newrange(self, w_start, w_end, inclusive):
        return W_RangeObject(w_start, w_end, inclusive)

    def newregexp(self, regexp):
        return W_RegexpObject(regexp)

    def newmodule(self, name):
        return W_ModuleObject(self, name)

    def newclass(self, name, superclass, is_singleton=False):
        return W_ClassObject(self, name, superclass, is_singleton=is_singleton)

    def newfunction(self, w_name, w_code):
        name = self.symbol_w(w_name)
        assert isinstance(w_code, W_CodeObject)
        return W_UserFunction(name, w_code)

    def newproc(self, block, is_lambda=False):
        return W_ProcObject(block, is_lambda)

    def int_w(self, w_obj):
        return w_obj.int_w(self)

    def float_w(self, w_obj):
        return w_obj.float_w(self)

    def symbol_w(self, w_obj):
        return w_obj.symbol_w(self)

    def str_w(self, w_obj):
        """Unpacks a string object as an rstr."""
        return w_obj.str_w(self)

    def listview(self, w_obj):
        return w_obj.listview(self)

    # Methods for implementing the language semantics.

    def is_true(self, w_obj):
        return w_obj.is_true(self)

    def getclass(self, w_receiver):
        return w_receiver.getclass(self)

    def getsingletonclass(self, w_receiver):
        return w_receiver.getsingletonclass(self)

    def getclassfor(self, cls):
        return self.getclassobject(cls.classdef)

    def getclassobject(self, classdef):
        return self.fromcache(ClassCache).getorbuild(classdef)

    def getmoduleobject(self, moduledef):
        return self.fromcache(ModuleCache).getorbuild(moduledef)

    def find_const(self, module, name):
        return module.find_const(self, name)

    def set_const(self, module, name, w_value):
        module.set_const(self, name, w_value)

    def find_instance_var(self, w_obj, name):
        return w_obj.find_instance_var(self, name)

    def set_instance_var(self, w_obj, name, w_value):
        w_obj.set_instance_var(self, name, w_value)

    def send(self, ec, w_receiver, w_method, args_w=None, block=None):
        if args_w is None:
            args_w = []
        name = self.symbol_w(w_method)

        w_cls = self.getclass(w_receiver)
        raw_method = w_cls.find_method(self, name)
        if raw_method is None:
            self.raise_(ec, self.getclassfor(W_NoMethodError), "undefined method `%s`" % name)
        return raw_method.call(ec, w_receiver, args_w, block)

    def respond_to(self, w_receiver, w_method):
        name = self.symbol_w(w_method)
        w_cls = self.getclass(w_receiver)
        raw_method = w_cls.find_method(self, name)
        return raw_method is not None

    @jit.unroll_safe
    def invoke_block(self, ec, block, args_w):
        bc = block.bytecode
        frame = self.create_frame(
            bc, w_self=block.w_self, w_scope=block.w_scope, block=block.block,
            parent_interp=block.parent_interp,
        )
        if (len(args_w) == 1 and
            isinstance(args_w[0], W_ArrayObject) and len(bc.arg_locs) >= 2):
            w_arg = args_w[0]
            assert isinstance(w_arg, W_ArrayObject)
            args_w = w_arg.items_w
        if len(bc.arg_locs) != 0:
            frame.handle_args(ec, bc, args_w, None)
        assert len(block.cells) == len(bc.freevars)
        for idx, cell in enumerate(block.cells):
            frame.cells[len(bc.cellvars) + idx] = cell

        with ec.visit_frame(frame):
            return ec.space.execute_frame(ec, frame, bc)

    def raise_(self, ec, w_type, msg=""):
        w_new_sym = self.newsymbol("new")
        w_exc = self.send(ec, w_type, w_new_sym, [self.newstr_fromstr(msg)])
        assert isinstance(w_exc, W_ExceptionObject)
        raise RubyError(w_exc)
