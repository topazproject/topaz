from __future__ import absolute_import

import os

from pypy.rlib import jit
from pypy.rlib.objectmodel import specialize
from pypy.rlib.parsing.parsing import ParseError
from pypy.tool.cache import Cache

from rupypy.astcompiler import CompilerContext, SymbolTable
from rupypy.celldict import CellDict
from rupypy.error import RubyError
from rupypy.executioncontext import ExecutionContext
from rupypy.frame import Frame
from rupypy.interpreter import Interpreter
from rupypy.lexer import LexerError
from rupypy.lib.dir import W_Dir
from rupypy.lib.random import W_Random
from rupypy.module import ClassCache, ModuleCache
from rupypy.modules.comparable import Comparable
from rupypy.modules.enumerable import Enumerable
from rupypy.modules.math import Math
from rupypy.modules.kernel import Kernel
from rupypy.modules.process import Process
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.boolobject import W_TrueObject, W_FalseObject
from rupypy.objects.classobject import W_ClassObject
from rupypy.objects.codeobject import W_CodeObject
from rupypy.objects.fileobject import W_FileObject, W_IOObject
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.functionobject import W_UserFunction
from rupypy.objects.exceptionobject import (W_ExceptionObject, W_NoMethodError,
    W_ZeroDivisionError, W_SyntaxError, W_LoadError, W_TypeError,
    W_ArgumentError, W_RuntimeError, W_StandardError)
from rupypy.objects.hashobject import W_HashObject
from rupypy.objects.intobject import W_FixnumObject
from rupypy.objects.integerobject import W_IntegerObject
from rupypy.objects.numericobject import W_NumericObject
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.nilobject import W_NilObject
from rupypy.objects.objectobject import W_Object, W_BaseObject
from rupypy.objects.procobject import W_ProcObject
from rupypy.objects.rangeobject import W_RangeObject
from rupypy.objects.regexpobject import W_RegexpObject
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.symbolobject import W_SymbolObject
from rupypy.objects.timeobject import W_TimeObject
from rupypy.parser import Transformer, _parse, ToASTVisitor


class SpaceCache(Cache):
    def __init__(self, space):
        Cache.__init__(self)
        self.space = space

    def _build(self, obj):
        return obj(self.space)


class ObjectSpace(object):
    def __init__(self):
        self.cache = SpaceCache(self)
        self.symbol_cache = {}
        self._executioncontext = None
        self.globals = CellDict()
        self.bootstrap = True
        self.w_top_self = W_Object(self, self.getclassfor(W_Object))

        self.w_true = W_TrueObject(self)
        self.w_false = W_FalseObject(self)
        self.w_nil = W_NilObject(self)

        # This is bootstrap. We have to delay sending until true, false and nil
        # are defined
        w_mod = self.getmoduleobject(Kernel.moduledef)
        self.send(self.getclassfor(W_Object), self.newsymbol("include"), [w_mod])
        self.bootstrap = False

        for cls in [
            W_NilObject, W_TrueObject, W_FalseObject,
            W_BaseObject, W_Object,
            W_StringObject, W_SymbolObject,
            W_NumericObject, W_IntegerObject, W_FloatObject, W_FixnumObject,
            W_ArrayObject, W_HashObject,
            W_IOObject, W_FileObject,
            W_ExceptionObject, W_NoMethodError, W_LoadError, W_ZeroDivisionError, W_SyntaxError,
            W_TypeError, W_ArgumentError, W_RuntimeError, W_StandardError,
            W_Random, W_Dir, W_ProcObject, W_TimeObject
        ]:
            self.add_class(cls)

        for module in [Math, Comparable, Enumerable, Kernel, Process]:
            self.add_module(module)

        w_load_path = self.newarray([
            self.newstr_fromstr(
                os.path.join(os.path.dirname(__file__), os.path.pardir, "lib-ruby")
            )
        ])
        self.globals.set("$LOAD_PATH", w_load_path)
        self.globals.set("$:", w_load_path)

        w_loaded_features = self.newarray([])
        self.globals.set("$LOADED_FEATURES", w_loaded_features)
        self.globals.set('$"', w_loaded_features)

    def _freeze_(self):
        return True

    @specialize.memo()
    def fromcache(self, key):
        return self.cache.getorbuild(key)

    # Setup methods

    def add_module(self, module):
        "NOT_RPYTHON"
        w_cls = self.getclassfor(W_Object)
        self.set_const(w_cls,
            module.moduledef.name, self.getmoduleobject(module.moduledef)
        )

    def add_class(self, cls):
        "NOT_RPYTHON"
        w_cls = self.getclassfor(W_Object)
        self.set_const(w_cls, cls.classdef.name, self.getclassfor(cls))

    # Methods for dealing with source code.

    def parse(self, source, initial_lineno=1):
        try:
            st = ToASTVisitor().transform(_parse(source, initial_lineno=initial_lineno))
            return Transformer().visit_main(st)
        except ParseError as e:
            raise self.error(self.getclassfor(W_SyntaxError), "line %d" % e.source_pos.lineno)
        except LexerError:
            raise self.error(self.getclassfor(W_SyntaxError))

    def compile(self, source, filepath, initial_lineno=1):
        astnode = self.parse(source, initial_lineno=initial_lineno)
        symtable = SymbolTable()
        astnode.locate_symbols(symtable)
        c = CompilerContext(self, "<main>", symtable, filepath)
        astnode.compile(c)
        return c.create_bytecode([], [], None, None)

    def execute(self, source, w_self=None, w_scope=None, filepath="-e", initial_lineno=1):
        bc = self.compile(source, filepath, initial_lineno=initial_lineno)
        frame = self.create_frame(bc, w_self=w_self, w_scope=w_scope)
        with self.getexecutioncontext().visit_frame(frame):
            return self.execute_frame(frame, bc)

    @jit.loop_invariant
    def getexecutioncontext(self):
        # When we have threads this should become a thread local.
        if self._executioncontext is None:
            self._executioncontext = ExecutionContext(self)
        return self._executioncontext

    def create_frame(self, bc, w_self=None, w_scope=None, block=None,
        parent_interp=None):

        if w_self is None:
            w_self = self.w_top_self
        if w_scope is None:
            w_scope = self.getclassfor(W_Object)
        return Frame(jit.promote(bc), w_self, w_scope, block, parent_interp)

    def execute_frame(self, frame, bc):
        return Interpreter().interpret(self, frame, bc)

    # Methods for allocating new objects.

    def newbool(self, boolvalue):
        if boolvalue:
            return self.w_true
        else:
            return self.w_false

    def newint(self, intvalue):
        return W_FixnumObject(self, intvalue)

    def newfloat(self, floatvalue):
        return W_FloatObject(self, floatvalue)

    @jit.elidable
    def newsymbol(self, symbol):
        try:
            w_sym = self.symbol_cache[symbol]
        except KeyError:
            w_sym = self.symbol_cache[symbol] = W_SymbolObject(self, symbol)
        return w_sym

    def newstr_fromchars(self, chars):
        return W_StringObject.newstr_fromchars(self, chars)

    def newstr_fromstr(self, strvalue):
        return W_StringObject.newstr_fromstr(self, strvalue)

    def newarray(self, items_w):
        return W_ArrayObject(self, items_w)

    def newhash(self):
        return W_HashObject(self)

    def newrange(self, w_start, w_end, exclusive):
        return W_RangeObject(self, w_start, w_end, exclusive)

    def newregexp(self, regexp):
        return W_RegexpObject(self, regexp)

    def newmodule(self, name):
        return W_ModuleObject(self, name, self.getclassfor(W_Object))

    def newclass(self, name, superclass, is_singleton=False):
        return W_ClassObject(self, name, superclass, is_singleton=is_singleton)

    def newfunction(self, w_name, w_code):
        name = self.symbol_w(w_name)
        assert isinstance(w_code, W_CodeObject)
        return W_UserFunction(name, w_code)

    def newproc(self, block, is_lambda=False):
        return W_ProcObject(self, block, is_lambda)

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

    def getscope(self, w_receiver):
        if isinstance(w_receiver, W_ModuleObject):
            return w_receiver
        else:
            return self.getclass(w_receiver)

    @jit.unroll_safe
    def getnonsingletonclass(self, w_receiver):
        cls = self.getclass(w_receiver)
        while cls.is_singleton:
            cls = cls.superclass
        return cls

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

    def set_lexical_scope(self, module, scope):
        module.set_lexical_scope(self, scope)

    def find_instance_var(self, w_obj, name):
        return w_obj.find_instance_var(self, name)

    def set_instance_var(self, w_obj, name, w_value):
        w_obj.set_instance_var(self, name, w_value)

    def find_class_var(self, w_module, name):
        return w_module.find_class_var(self, name)

    def set_class_var(self, w_module, name, w_value):
        w_module.set_class_var(self, name, w_value)

    def send(self, w_receiver, w_method, args_w=None, block=None):
        if args_w is None:
            args_w = []
        name = self.symbol_w(w_method)

        w_cls = self.getclass(w_receiver)
        raw_method = w_cls.find_method(self, name)
        if raw_method is None:
            method_missing = w_cls.find_method(self, "method_missing")
            assert method_missing is not None
            args_w.insert(0, w_method)
            return method_missing.call(self, w_receiver, args_w, block)
        return raw_method.call(self, w_receiver, args_w, block)

    def respond_to(self, w_receiver, w_method):
        name = self.symbol_w(w_method)
        w_cls = self.getclass(w_receiver)
        raw_method = w_cls.find_method(self, name)
        return raw_method is not None

    @jit.unroll_safe
    def invoke_block(self, block, args_w):
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
            frame.handle_args(self, bc, args_w, None)
        assert len(block.cells) == len(bc.freevars)
        for idx, cell in enumerate(block.cells):
            frame.cells[len(bc.cellvars) + idx] = cell

        with self.getexecutioncontext().visit_frame(frame):
            return self.execute_frame(frame, bc)

    def error(self, w_type, msg=""):
        w_new_sym = self.newsymbol("new")
        w_exc = self.send(w_type, w_new_sym, [self.newstr_fromstr(msg)])
        assert isinstance(w_exc, W_ExceptionObject)
        return RubyError(w_exc)

    def hash_w(self, w_obj):
        return self.int_w(self.send(w_obj, self.newsymbol("hash")))

    def eq_w(self, w_obj1, w_obj2):
        return self.is_true(self.send(w_obj1, self.newsymbol("=="), [w_obj2]))

    def subscript_access(self, length, w_idx, w_count):
        inclusive = False
        as_range = False
        end = 0
        fixnum_class = self.getclassfor(W_FixnumObject)

        if isinstance(w_idx, W_RangeObject) and not w_count:
            start = self.int_w(self.convert_type(w_idx.w_start, fixnum_class, "to_int"))
            end = self.int_w(self.convert_type(w_idx.w_end, fixnum_class, "to_int"))
            inclusive = not w_idx.exclusive
            as_range = True
        else:
            start = self.int_w(self.convert_type(w_idx, fixnum_class, "to_int"))
            if w_count:
                end = self.int_w(self.convert_type(w_count, fixnum_class, "to_int"))
                if end < 0:
                    end = -1
                else:
                    as_range = True

        if start < 0:
            start += length
        if as_range:
            if w_count:
                end += start
            if end < 0:
                end += length
            if inclusive:
                end += 1
            if end < start:
                end = start
            elif end > length:
                end = length
        return (start, end, as_range)

    def convert_type(self, w_obj, w_cls, method, raise_error=True):
        if w_obj.is_kind_of(self, w_cls):
            return w_obj

        try:
            w_res = self.send(w_obj, self.newsymbol(method))
        except RubyError:
            src_cls = self.getclass(w_obj).name
            raise self.error(
                self.getclassfor(W_TypeError),
                "can't convert %s into %s" % (src_cls, w_cls.name)
            )

        if not w_res or w_res is self.w_nil and not raise_error:
            return self.w_nil
        elif not w_res.is_kind_of(self, w_cls):
            src_cls = self.getclass(w_obj).name
            res_cls = self.getclass(w_res).name
            raise self.error(
                self.getclassfor(W_TypeError),
                "can't convert %s to %s (%s#%s gives %s)" % (
                    src_cls, w_cls.name, src_cls, method, res_cls
                )
            )
        else:
            return w_res
