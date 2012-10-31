from __future__ import absolute_import

import os

from pypy.rlib import jit
from pypy.rlib.objectmodel import specialize
from pypy.tool.cache import Cache

from rply.errors import ParsingError

from rupypy.astcompiler import CompilerContext, SymbolTable
from rupypy.celldict import CellDict
from rupypy.error import RubyError, print_traceback
from rupypy.executioncontext import ExecutionContext
from rupypy.frame import Frame
from rupypy.interpreter import Interpreter
from rupypy.lexer import LexerError, Lexer
from rupypy.lib.dir import W_Dir
from rupypy.lib.random import W_RandomObject
from rupypy.module import ClassCache, ModuleCache
from rupypy.modules.comparable import Comparable
from rupypy.modules.enumerable import Enumerable
from rupypy.modules.math import Math
from rupypy.modules.kernel import Kernel
from rupypy.modules.process import Process
from rupypy.modules.topaz import Topaz
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.bignumobject import W_BignumObject
from rupypy.objects.boolobject import W_TrueObject, W_FalseObject
from rupypy.objects.classobject import W_ClassObject
from rupypy.objects.codeobject import W_CodeObject
from rupypy.objects.encodingobject import W_EncodingObject
from rupypy.objects.envobject import W_EnvObject
from rupypy.objects.exceptionobject import (W_ExceptionObject, W_NoMethodError,
    W_ZeroDivisionError, W_SyntaxError, W_LoadError, W_TypeError,
    W_ArgumentError, W_RuntimeError, W_StandardError, W_SystemExit,
    W_SystemCallError, W_NameError, W_IndexError, W_StopIteration,
    W_NotImplementedError, W_RangeError, W_LocalJumpError)
from rupypy.objects.fileobject import W_FileObject, W_IOObject
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.functionobject import W_UserFunction
from rupypy.objects.hashobject import W_HashObject, W_HashIterator
from rupypy.objects.intobject import W_FixnumObject
from rupypy.objects.integerobject import W_IntegerObject
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.nilobject import W_NilObject
from rupypy.objects.numericobject import W_NumericObject
from rupypy.objects.objectobject import W_Object, W_BaseObject
from rupypy.objects.procobject import W_ProcObject
from rupypy.objects.rangeobject import W_RangeObject
from rupypy.objects.regexpobject import W_RegexpObject
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.symbolobject import W_SymbolObject
from rupypy.objects.threadobject import W_ThreadObject
from rupypy.objects.timeobject import W_TimeObject
from rupypy.parser import Parser


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
        self.exit_handlers_w = []

        self.w_true = W_TrueObject(self)
        self.w_false = W_FalseObject(self)
        self.w_nil = W_NilObject(self)

        # Force the setup of a few key classes, we create a fake "Class" class
        # for the initial bootstrap.
        self.w_class = self.newclass("FakeClass", None)
        self.w_basicobject = self.getclassfor(W_BaseObject)
        self.w_object = self.getclassfor(W_Object)
        self.w_class = self.getclassfor(W_ClassObject)
        # We replace the one reference to our FakeClass with the real class.
        self.w_basicobject.klass.superclass = self.w_class

        self.w_symbol = self.getclassfor(W_SymbolObject)
        self.w_array = self.getclassfor(W_ArrayObject)
        self.w_proc = self.getclassfor(W_ProcObject)
        self.w_numeric = self.getclassfor(W_NumericObject)
        self.w_fixnum = self.getclassfor(W_FixnumObject)
        self.w_float = self.getclassfor(W_FloatObject)
        self.w_bignum = self.getclassfor(W_BignumObject)
        self.w_integer = self.getclassfor(W_IntegerObject)
        self.w_module = self.getclassfor(W_ModuleObject)
        self.w_string = self.getclassfor(W_StringObject)
        self.w_hash = self.getclassfor(W_HashObject)
        self.w_NoMethodError = self.getclassfor(W_NoMethodError)
        self.w_ArgumentError = self.getclassfor(W_ArgumentError)
        self.w_LocalJumpError = self.getclassfor(W_LocalJumpError)
        self.w_NameError = self.getclassfor(W_NameError)
        self.w_NotImplementedError = self.getclassfor(W_NotImplementedError)
        self.w_IndexError = self.getclassfor(W_IndexError)
        self.w_LoadError = self.getclassfor(W_LoadError)
        self.w_RangeError = self.getclassfor(W_RangeError)
        self.w_RuntimeError = self.getclassfor(W_RuntimeError)
        self.w_StandardError = self.getclassfor(W_StandardError)
        self.w_StopIteration = self.getclassfor(W_StopIteration)
        self.w_SyntaxError = self.getclassfor(W_SyntaxError)
        self.w_SystemCallError = self.getclassfor(W_SystemCallError)
        self.w_SystemExit = self.getclassfor(W_SystemExit)
        self.w_TypeError = self.getclassfor(W_TypeError)
        self.w_ZeroDivisionError = self.getclassfor(W_ZeroDivisionError)
        self.w_kernel = self.getmoduleobject(Kernel.moduledef)

        self.w_topaz = self.getmoduleobject(Topaz.moduledef)

        for w_cls in [
            self.w_basicobject, self.w_object, self.w_array, self.w_proc,
            self.w_numeric, self.w_fixnum, self.w_float, self.w_string,
            self.w_symbol, self.w_class, self.w_module, self.w_hash,

            self.w_NoMethodError, self.w_ArgumentError, self.w_TypeError,
            self.w_ZeroDivisionError, self.w_SystemExit, self.w_RangeError,
            self.w_RuntimeError, self.w_SystemCallError, self.w_LoadError,
            self.w_StopIteration, self.w_SyntaxError, self.w_NameError,
            self.w_StandardError, self.w_LocalJumpError,

            self.w_kernel, self.w_topaz,

            self.getclassfor(W_NilObject),
            self.getclassfor(W_TrueObject),
            self.getclassfor(W_FalseObject),
            self.getclassfor(W_RangeObject),
            self.getclassfor(W_IOObject),
            self.getclassfor(W_FileObject),
            self.getclassfor(W_Dir),
            self.getclassfor(W_EncodingObject),
            self.getclassfor(W_RandomObject),
            self.getclassfor(W_ThreadObject),
            self.getclassfor(W_TimeObject),

            self.getclassfor(W_ExceptionObject),
            self.getclassfor(W_StandardError),

            self.getmoduleobject(Comparable.moduledef),
            self.getmoduleobject(Enumerable.moduledef),
            self.getmoduleobject(Math.moduledef),
            self.getmoduleobject(Process.moduledef),
        ]:
            self.set_const(
                self.w_object,
                self.str_w(self.send(w_cls, self.newsymbol("name"))),
                w_cls
            )

        for w_cls in [
            self.getclassfor(W_EnvObject), self.getclassfor(W_HashIterator),
        ]:
            self.set_const(
                self.w_topaz,
                self.str_w(self.send(w_cls, self.newsymbol("name"))),
                w_cls
            )

        # This is bootstrap. We have to delay sending until true, false and nil
        # are defined
        self.send(self.w_object, self.newsymbol("include"), [self.w_kernel])
        self.bootstrap = False

        w_load_path = self.newarray([
            self.newstr_fromstr(os.path.abspath(
                os.path.join(os.path.dirname(__file__), os.path.pardir, "lib-ruby")
            ))
        ])
        self.globals.set("$LOAD_PATH", w_load_path)
        self.globals.set("$:", w_load_path)

        w_loaded_features = self.newarray([])
        self.globals.set("$LOADED_FEATURES", w_loaded_features)
        self.globals.set('$"', w_loaded_features)

        self.w_main_thread = W_ThreadObject(self)

        # TODO: this should really go in a better place.
        self.execute("""
        def self.include *mods
            Object.include *mods
        end
        """)

    def _freeze_(self):
        return True

    @specialize.memo()
    def fromcache(self, key):
        return self.cache.getorbuild(key)

    # Methods for dealing with source code.

    def parse(self, source, initial_lineno=1, symtable=None):
        if symtable is None:
            symtable = SymbolTable()
        parser = Parser(Lexer(source, initial_lineno=initial_lineno, symtable=symtable))
        try:
            return parser.parse().getast()
        except ParsingError as e:
            raise self.error(self.w_SyntaxError, "line %d" % e.getsourcepos().lineno)
        except LexerError as e:
            raise self.error(self.w_SyntaxError, "line %d" % e.pos.lineno)

    def compile(self, source, filepath, initial_lineno=1):
        symtable = SymbolTable()
        astnode = self.parse(source, initial_lineno=initial_lineno, symtable=symtable)
        ctx = CompilerContext(self, "<main>", symtable, filepath)
        with ctx.set_lineno(initial_lineno):
            astnode.compile(ctx)
        return ctx.create_bytecode([], [], None, None)

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

    def create_frame(self, bc, w_self=None, w_scope=None, lexical_scope=None,
        block=None, parent_interp=None):

        if w_self is None:
            w_self = self.w_top_self
        if w_scope is None:
            w_scope = self.w_object
        return Frame(jit.promote(bc), w_self, w_scope, lexical_scope, block, parent_interp)

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

    def newbigint_fromint(self, intvalue):
        return W_BignumObject.newbigint_fromint(self, intvalue)

    def newbigint_fromrbigint(self, bigint):
        return W_BignumObject.newbigint_fromrbigint(self, bigint)

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

    def newstr_fromstrs(self, strs_w):
        return W_StringObject.newstr_fromstrs(self, strs_w)

    def newarray(self, items_w):
        return W_ArrayObject(self, items_w)

    def newhash(self):
        return W_HashObject(self)

    def newrange(self, w_start, w_end, exclusive):
        return W_RangeObject(self, w_start, w_end, exclusive)

    def newregexp(self, regexp):
        return W_RegexpObject(self, regexp)

    def newmodule(self, name):
        return W_ModuleObject(self, name)

    def newclass(self, name, superclass, is_singleton=False):
        return W_ClassObject(self, name, superclass, is_singleton=is_singleton)

    def newfunction(self, w_name, w_code, lexical_scope):
        name = self.symbol_w(w_name)
        assert isinstance(w_code, W_CodeObject)
        return W_UserFunction(name, w_code, lexical_scope)

    def newproc(self, block, is_lambda=False):
        return W_ProcObject(self, block, is_lambda)

    def int_w(self, w_obj):
        return w_obj.int_w(self)

    def bigint_w(self, w_obj):
        return w_obj.bigint_w(self)

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

    def find_const(self, w_module, name):
        w_res = w_module.find_const(self, name)
        if w_res is None:
            w_res = self.send(w_module, self.newsymbol("const_missing"), [self.newsymbol(name)])
        return w_res

    def set_const(self, module, name, w_value):
        module.set_const(self, name, w_value)

    @jit.unroll_safe
    def find_lexical_const(self, lexical_scope, name):
        w_res = None
        scope = lexical_scope
        while scope is not None:
            w_mod = scope.w_mod
            w_res = w_mod.find_local_const(self, name)
            if w_res is not None:
                return w_res
            scope = scope.backscope
        if lexical_scope is not None:
            w_res = lexical_scope.w_mod.find_const(self, name)
        if w_res is None:
            w_res = self.w_object.find_const(self, name)
        if w_res is None:
            if lexical_scope is not None:
                w_mod = lexical_scope.w_mod
            else:
                w_mod = self.w_object
            w_res = self.send(w_mod, self.newsymbol("const_missing"), [self.newsymbol(name)])
        return w_res

    def find_instance_var(self, w_obj, name):
        w_res = w_obj.find_instance_var(self, name)
        return w_res if w_res is not None else self.w_nil

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
        return self._send_raw(w_method, raw_method, w_receiver, w_cls, args_w, block)

    def send_super(self, w_cls, w_receiver, w_method, args_w, block=None):
        name = self.symbol_w(w_method)
        raw_method = w_cls.find_method_super(self, name)
        return self._send_raw(w_method, raw_method, w_receiver, w_cls, args_w, block)

    def _send_raw(self, w_method, raw_method, w_receiver, w_cls, args_w, block):
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

    def is_kind_of(self, w_obj, w_cls):
        return w_obj.is_kind_of(self, w_cls)

    @jit.unroll_safe
    def invoke_block(self, block, args_w):
        bc = block.bytecode
        frame = self.create_frame(
            bc, w_self=block.w_self, w_scope=block.w_scope,
            lexical_scope=block.lexical_scope, block=block.block,
            parent_interp=block.parent_interp,
        )
        if (len(args_w) == 1 and
            isinstance(args_w[0], W_ArrayObject) and len(bc.arg_locs) >= 2):
            w_arg = args_w[0]
            assert isinstance(w_arg, W_ArrayObject)
            args_w = w_arg.items_w
        if len(bc.arg_locs) != 0:
            frame.handle_block_args(self, bc, args_w, None)
        assert len(block.cells) == len(bc.freevars)
        for idx, cell in enumerate(block.cells):
            frame.cells[len(bc.cellvars) + idx] = cell

        with self.getexecutioncontext().visit_frame(frame):
            return self.execute_frame(frame, bc)

    def error(self, w_type, msg="", optargs=None):
        if not optargs:
            optargs = []
        w_new_sym = self.newsymbol("new")
        args_w = [self.newstr_fromstr(msg)] + optargs
        w_exc = self.send(w_type, w_new_sym, args_w)
        assert isinstance(w_exc, W_ExceptionObject)
        return RubyError(w_exc)

    def hash_w(self, w_obj):
        return self.int_w(self.send(w_obj, self.newsymbol("hash")))

    def eq_w(self, w_obj1, w_obj2):
        return self.is_true(self.send(w_obj1, self.newsymbol("eql?"), [w_obj2]))

    def register_exit_handler(self, w_proc):
        self.exit_handlers_w.append(w_proc)

    def run_exit_handlers(self):
        while self.exit_handlers_w:
            w_proc = self.exit_handlers_w.pop()
            try:
                self.send(w_proc, self.newsymbol("call"))
            except RubyError as e:
                print_traceback(self, e.w_value)

    def subscript_access(self, length, w_idx, w_count):
        inclusive = False
        as_range = False
        end = 0

        if isinstance(w_idx, W_RangeObject) and not w_count:
            start = self.int_w(self.convert_type(w_idx.w_start, self.w_fixnum, "to_int"))
            end = self.int_w(self.convert_type(w_idx.w_end, self.w_fixnum, "to_int"))
            inclusive = not w_idx.exclusive
            as_range = True
        else:
            start = self.int_w(self.convert_type(w_idx, self.w_fixnum, "to_int"))
            if w_count:
                end = self.int_w(self.convert_type(w_count, self.w_fixnum, "to_int"))
                if end >= 0:
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

        nil = ((not as_range and start >= length) or
            start < 0 or end < 0 or (start > 0 and start > length))
        return (start, end, as_range, nil)

    def convert_type(self, w_obj, w_cls, method, raise_error=True):
        if self.is_kind_of(w_obj, w_cls):
            return w_obj

        try:
            w_res = self.send(w_obj, self.newsymbol(method))
        except RubyError:
            if not raise_error:
                return self.w_nil
            src_cls = self.getclass(w_obj).name
            raise self.error(
                self.w_TypeError, "can't convert %s into %s" % (src_cls, w_cls.name)
            )

        if not w_res or w_res is self.w_nil and not raise_error:
            return self.w_nil
        elif not self.is_kind_of(w_res, w_cls):
            src_cls = self.getclass(w_obj).name
            res_cls = self.getclass(w_res).name
            raise self.error(self.w_TypeError,
                "can't convert %s to %s (%s#%s gives %s)" % (
                    src_cls, w_cls.name, src_cls, method, res_cls
                )
            )
        else:
            return w_res
