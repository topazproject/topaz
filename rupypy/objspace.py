from __future__ import absolute_import

from pypy.rlib import jit
from pypy.rlib.objectmodel import specialize
from pypy.tool.cache import Cache

from rupypy.astcompiler import CompilerContext, SymbolTable
from rupypy.interpreter import Interpreter, Frame
from rupypy.lib.random import W_Random
from rupypy.module import ClassCache, Function
from rupypy.modules.math import Math
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.boolobject import W_TrueObject, W_FalseObject
from rupypy.objects.classobject import W_ClassObject
from rupypy.objects.codeobject import W_CodeObject
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.exceptionobject import W_ZeroDivisionError
from rupypy.objects.intobject import W_IntObject
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.nilobject import W_NilObject
from rupypy.objects.objectobject import W_Object
from rupypy.objects.rangeobject import W_RangeObject
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.symbolobject import W_SymbolObject
from rupypy.parser import Transformer, _parse, to_ast


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
        self.w_top_self = self.send(self.getclassfor(W_Object), self.newsymbol("new"))

        self.w_true = W_TrueObject()
        self.w_false = W_FalseObject()
        self.w_nil = W_NilObject()

        for cls in [W_ZeroDivisionError, W_Random]:
            self.add_class(cls)

        for module in [Math]:
            self.add_module(module)

        self.w_ZeroDivisionError = self.getclassfor(W_ZeroDivisionError)

    def _freeze_(self):
        return True

    @specialize.memo()
    def fromcache(self, key):
        return self.cache.getorbuild(key)

    # Setup methods

    def add_module(self, module):
        w_module = module.build_object(self)
        self.set_const(self.getclassfor(W_Object), module.moduledef.name, w_module)

    def add_class(self, cls):
        self.set_const(self.getclassfor(W_Object), cls.classdef.name, self.getclassfor(cls))

    # Methods for dealing with source code.

    def parse(self, source):
        return self.transformer.visit_main(to_ast().transform(_parse(source)))

    def compile(self, source, filepath):
        astnode = self.parse(source)
        symtable = SymbolTable()
        astnode.locate_symbols(symtable)
        c = CompilerContext(self, symtable, filepath)
        astnode.compile(c)
        return c.create_bytecode("<string>", [], [])

    def execute(self, source, w_self=None, filepath="-e"):
        bc = self.compile(source, filepath)
        frame = self.create_frame(bc, w_self)
        return Interpreter().interpret(self, frame, bc)

    def create_frame(self, bc, w_self=None, w_scope=None, block=None):
        if w_self is None:
            w_self = self.w_top_self
        if w_scope is None:
            w_scope = self.getclassfor(W_Object)
        return Frame(jit.promote(bc), w_self, w_scope, block)

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

    def newrange(self, w_start, w_end, inclusive):
        return W_RangeObject(w_start, w_end, inclusive)

    def newmodule(self, name):
        return W_ModuleObject(self, name)

    def newclass(self, name, superclass, is_singleton=False):
        return W_ClassObject(self, name, superclass, is_singleton=is_singleton)

    def newfunction(self, w_name, w_code):
        name = self.symbol_w(w_name)
        assert isinstance(w_code, W_CodeObject)
        return Function(name, w_code)

    def int_w(self, w_obj):
        return w_obj.int_w(self)

    def float_w(self, w_obj):
        return w_obj.float_w(self)

    def symbol_w(self, w_obj):
        return w_obj.symbol_w(self)

    def str_w(self, w_obj):
        """Unpacks a string object as an rstr."""
        return w_obj.str_w(self)

    def liststr_w(self, w_obj):
        """Unpacks a string object as an rlist of chars"""
        return w_obj.liststr_w(self)

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

    def find_const(self, module, name):
        return module.find_const(self, name)

    def set_const(self, module, name, w_value):
        module.set_const(self, name, w_value)

    def find_instance_var(self, w_obj, name):
        return w_obj.find_instance_var(self, name)

    def set_instance_var(self, w_obj, name, w_value):
        w_obj.set_instance_var(self, name, w_value)

    def send(self, w_receiver, w_method, args_w=None, block=None):
        if args_w is None:
            args_w = []
        name = self.symbol_w(w_method)

        w_cls = self.getclass(w_receiver)
        raw_method = w_cls.find_method(self, name)
        if raw_method is None:
            raise LookupError(name)
        return raw_method.call(self, w_receiver, args_w, block)

    @jit.unroll_safe
    def invoke_block(self, block, args_w):
        bc = block.bytecode
        frame = self.create_frame(bc, w_self=block.w_self, w_scope=block.w_scope, block=block.block)
        if len(args_w) == 1 and isinstance(args_w[0], W_ArrayObject) and len(bc.arg_locs) >= 2:
            w_arg = args_w[0]
            assert isinstance(w_arg, W_ArrayObject)
            args_w = w_arg.items_w
        if len(bc.arg_locs) != 0:
            frame.handle_args(self, bc, args_w)
        assert len(block.cells) == len(bc.freevars)
        for idx, cell in enumerate(block.cells):
            frame.cells[len(bc.cellvars) + idx] = cell
        return Interpreter().interpret(self, frame, bc)
