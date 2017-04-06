from __future__ import absolute_import

import gc
import os
import sys
import weakref

from rpython.rlib import jit, rpath, types
from rpython.rlib.cache import Cache
from rpython.rlib.objectmodel import specialize, compute_unique_id
from rpython.rlib.signature import signature
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.rbigint import rbigint
from rpython.rtyper.lltypesystem import llmemory, rffi

from rply.errors import ParsingError

from topaz import system
from topaz.astcompiler import CompilerContext, SymbolTable, CompilerError
from topaz.celldict import GlobalsDict
from topaz.closure import ClosureCell
from topaz.error import RubyError, print_traceback
from topaz.executioncontext import ExecutionContext, ExecutionContextHolder
from topaz.frame import Frame
from topaz.interpreter import Interpreter
from topaz.lexer import LexerError, Lexer
from topaz.module import ClassCache, ModuleCache
from topaz.modules.comparable import Comparable
from topaz.modules.enumerable import Enumerable
from topaz.modules.marshal import Marshal
from topaz.modules.math import Math
from topaz.modules.kernel import Kernel
from topaz.modules.fcntl import Fcntl
from topaz.modules.ffi import FFI
from topaz.modules.objectspace import ObjectSpace as ObjectSpaceModule
from topaz.modules.process import Process
from topaz.modules.signal import Signal
from topaz.modules.topaz import Topaz
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.bignumobject import W_BignumObject
from topaz.objects.bindingobject import W_BindingObject
from topaz.objects.boolobject import W_TrueObject, W_FalseObject
from topaz.objects.classobject import W_ClassObject
from topaz.objects.codeobject import W_CodeObject
from topaz.objects.dirobject import W_DirObject
from topaz.objects.encodingobject import W_EncodingObject
from topaz.objects.envobject import W_EnvObject
from topaz.objects.exceptionobject import (
    W_ExceptionObject, W_NoMethodError,
    W_ZeroDivisionError, W_SyntaxError, W_LoadError, W_TypeError,
    W_ArgumentError, W_RuntimeError, W_StandardError, W_SystemExit,
    W_SystemCallError, W_NameError, W_IndexError, W_KeyError, W_StopIteration,
    W_NotImplementedError, W_RangeError, W_LocalJumpError, W_IOError,
    W_RegexpError, W_ThreadError, W_FiberError, W_EOFError, W_FloatDomainError,
    W_SystemStackError)
from topaz.objects.fiberobject import W_FiberObject
from topaz.objects.fileobject import W_FileObject
from topaz.objects.floatobject import W_FloatObject
from topaz.objects.functionobject import W_UserFunction
from topaz.objects.hashobject import W_HashObject, W_HashIterator
from topaz.objects.integerobject import W_IntegerObject
from topaz.objects.intobject import W_FixnumObject
from topaz.objects.ioobject import W_IOObject
from topaz.objects.methodobject import W_MethodObject, W_UnboundMethodObject
from topaz.objects.moduleobject import W_ModuleObject
from topaz.objects.nilobject import W_NilObject
from topaz.objects.numericobject import W_NumericObject
from topaz.objects.objectobject import W_Object, W_BaseObject, W_Root
from topaz.objects.procobject import W_ProcObject
from topaz.objects.randomobject import W_RandomObject
from topaz.objects.rangeobject import W_RangeObject
from topaz.objects.regexpobject import W_RegexpObject, W_MatchDataObject
from topaz.objects.stringobject import W_StringObject
from topaz.objects.symbolobject import W_SymbolObject
from topaz.objects.threadobject import W_ThreadObject
from topaz.objects.timeobject import W_TimeObject
from topaz.parser import Parser
from topaz.utils.ll_file import isdir


class SpaceCache(Cache):
    def __init__(self, space):
        Cache.__init__(self)
        self.space = space

    def _build(self, obj):
        return obj(self.space)


class ObjectSpace(object):
    def __init__(self, config):
        self.config = config

        self.cache = SpaceCache(self)
        self.symbol_cache = {}
        self._executioncontexts = ExecutionContextHolder()
        self.globals = GlobalsDict()
        self.bootstrap = True
        self.exit_handlers_w = []

        self.w_true = W_TrueObject(self)
        self.w_false = W_FalseObject(self)
        self.w_nil = W_NilObject(self)

        # Force the setup of a few key classes, we create a fake "Class" class
        # for the initial bootstrap.
        self.w_class = self.newclass("FakeClass", None)
        cls_reference = weakref.ref(self.w_class)
        self.w_basicobject = self.getclassfor(W_BaseObject)
        self.w_object = self.getclassfor(W_Object)
        self.w_class = self.getclassfor(W_ClassObject)
        # We replace the one reference to our FakeClass with the real class.
        self.w_basicobject.klass.superclass = self.w_class

        gc.collect()
        assert cls_reference() is None

        self.w_symbol = self.getclassfor(W_SymbolObject)
        self.w_array = self.getclassfor(W_ArrayObject)
        self.w_proc = self.getclassfor(W_ProcObject)
        self.w_binding = self.getclassfor(W_BindingObject)
        self.w_numeric = self.getclassfor(W_NumericObject)
        self.w_fixnum = self.getclassfor(W_FixnumObject)
        self.w_float = self.getclassfor(W_FloatObject)
        self.w_bignum = self.getclassfor(W_BignumObject)
        self.w_integer = self.getclassfor(W_IntegerObject)
        self.w_module = self.getclassfor(W_ModuleObject)
        self.w_string = self.getclassfor(W_StringObject)
        self.w_regexp = self.getclassfor(W_RegexpObject)
        self.w_hash = self.getclassfor(W_HashObject)
        self.w_method = self.getclassfor(W_MethodObject)
        self.w_unbound_method = self.getclassfor(W_UnboundMethodObject)
        self.w_io = self.getclassfor(W_IOObject)
        self.w_NoMethodError = self.getclassfor(W_NoMethodError)
        self.w_ArgumentError = self.getclassfor(W_ArgumentError)
        self.w_LocalJumpError = self.getclassfor(W_LocalJumpError)
        self.w_NameError = self.getclassfor(W_NameError)
        self.w_NotImplementedError = self.getclassfor(W_NotImplementedError)
        self.w_IndexError = self.getclassfor(W_IndexError)
        self.w_KeyError = self.getclassfor(W_KeyError)
        self.w_IOError = self.getclassfor(W_IOError)
        self.w_EOFError = self.getclassfor(W_EOFError)
        self.w_FiberError = self.getclassfor(W_FiberError)
        self.w_LoadError = self.getclassfor(W_LoadError)
        self.w_RangeError = self.getclassfor(W_RangeError)
        self.w_FloatDomainError = self.getclassfor(W_FloatDomainError)
        self.w_RegexpError = self.getclassfor(W_RegexpError)
        self.w_RuntimeError = self.getclassfor(W_RuntimeError)
        self.w_StandardError = self.getclassfor(W_StandardError)
        self.w_StopIteration = self.getclassfor(W_StopIteration)
        self.w_SyntaxError = self.getclassfor(W_SyntaxError)
        self.w_SystemCallError = self.getclassfor(W_SystemCallError)
        self.w_SystemExit = self.getclassfor(W_SystemExit)
        self.w_SystemStackError = self.getclassfor(W_SystemStackError)
        self.w_TypeError = self.getclassfor(W_TypeError)
        self.w_ZeroDivisionError = self.getclassfor(W_ZeroDivisionError)
        self.w_kernel = self.getmoduleobject(Kernel.moduledef)

        self.w_topaz = self.getmoduleobject(Topaz.moduledef)

        for w_cls in [
            self.w_basicobject, self.w_object, self.w_array, self.w_proc,
            self.w_numeric, self.w_fixnum, self.w_bignum, self.w_float,
            self.w_string, self.w_symbol, self.w_class, self.w_module,
            self.w_hash, self.w_regexp, self.w_method, self.w_unbound_method,
            self.w_io, self.w_binding,

            self.w_NoMethodError, self.w_ArgumentError, self.w_TypeError,
            self.w_ZeroDivisionError, self.w_SystemExit, self.w_RangeError,
            self.w_RegexpError, self.w_RuntimeError, self.w_SystemCallError,
            self.w_LoadError, self.w_StopIteration, self.w_SyntaxError,
            self.w_NameError, self.w_StandardError, self.w_LocalJumpError,
            self.w_IndexError, self.w_IOError, self.w_NotImplementedError,
            self.w_EOFError, self.w_FloatDomainError, self.w_FiberError,
            self.w_SystemStackError, self.w_KeyError,

            self.w_kernel, self.w_topaz,

            self.getclassfor(W_NilObject),
            self.getclassfor(W_TrueObject),
            self.getclassfor(W_FalseObject),
            self.getclassfor(W_RangeObject),
            self.getclassfor(W_FileObject),
            self.getclassfor(W_DirObject),
            self.getclassfor(W_EncodingObject),
            self.getclassfor(W_IntegerObject),
            self.getclassfor(W_RandomObject),
            self.getclassfor(W_ThreadObject),
            self.getclassfor(W_TimeObject),
            self.getclassfor(W_MethodObject),
            self.getclassfor(W_UnboundMethodObject),
            self.getclassfor(W_FiberObject),
            self.getclassfor(W_MatchDataObject),

            self.getclassfor(W_ExceptionObject),
            self.getclassfor(W_ThreadError),

            self.getmoduleobject(Comparable.moduledef),
            self.getmoduleobject(Enumerable.moduledef),
            self.getmoduleobject(Marshal.moduledef),
            self.getmoduleobject(Math.moduledef),
            self.getmoduleobject(Fcntl.moduledef),
            self.getmoduleobject(FFI.moduledef),
            self.getmoduleobject(Process.moduledef),
            self.getmoduleobject(Signal.moduledef),
            self.getmoduleobject(ObjectSpaceModule.moduledef),
        ]:
            self.set_const(
                self.w_object,
                self.str_w(self.send(w_cls, "name")),
                w_cls
            )

        for w_cls in [
            self.getclassfor(W_EnvObject), self.getclassfor(W_HashIterator),
        ]:
            self.set_const(
                self.w_topaz,
                self.str_w(self.send(w_cls, "name")),
                w_cls
            )

        self.set_const(self.w_basicobject, "BasicObject", self.w_basicobject)

        # This is bootstrap. We have to delay sending until true, false and nil
        # are defined
        self.send(self.w_object, "include", [self.w_kernel])
        self.bootstrap = False

        self.w_load_path = self.newarray([])
        self.globals.define_virtual(
            "$LOAD_PATH", lambda space: space.w_load_path)
        self.globals.define_virtual("$:", lambda space: space.w_load_path)

        self.globals.define_virtual(
            "$$", lambda space: space.send(space.getmoduleobject(Process.moduledef), "pid"))

        self.w_loaded_features = self.newarray([])
        self.globals.define_virtual(
            "$LOADED_FEATURES", lambda space: space.w_loaded_features)
        self.globals.define_virtual(
            '$"', lambda space: space.w_loaded_features)

        self.w_main_thread = W_ThreadObject(self)

        self.w_load_path = self.newarray([])
        self.base_lib_path = os.path.abspath(os.path.join(os.path.join(
            os.path.dirname(__file__), os.path.pardir), "lib-ruby"))

    def _freeze_(self):
        self._executioncontexts.clear()
        return True

    def find_executable(self, executable):
        if os.sep in executable or (system.IS_WINDOWS and ":" in executable):
            return executable
        path = os.environ.get("PATH")
        if path:
            for dir in path.split(os.pathsep):
                f = os.path.join(dir, executable)
                if os.path.isfile(f):
                    executable = f
                    break
        return rpath.rabspath(executable)

    def setup(self, executable):
        """
        Performs runtime setup.
        """
        path = rpath.rabspath(self.find_executable(executable))
        # Fallback to a path relative to the compiled location.
        lib_path = self.base_lib_path
        kernel_path = os.path.join(
            os.path.join(lib_path, os.path.pardir), "lib-topaz")
        while True:
            par_path = rpath.rabspath(os.path.join(path, os.path.pardir))
            if par_path == path:
                break
            path = par_path
            if isdir(os.path.join(path, "lib-ruby")):
                lib_path = os.path.join(path, "lib-ruby")
                kernel_path = os.path.join(path, "lib-topaz")
                break
        self.send(self.w_load_path, "unshift", [self.newstr_fromstr(lib_path)])
        self.load_kernel(kernel_path)

        self.set_const(
            self.w_object,
            "RUBY_ENGINE", self.newstr_fromstr(system.RUBY_ENGINE))
        self.set_const(
            self.w_object,
            "RUBY_VERSION", self.newstr_fromstr(system.RUBY_VERSION))
        self.set_const(
            self.w_object,
            "RUBY_PATCHLEVEL", self.newint(system.RUBY_PATCHLEVEL))
        self.set_const(
            self.w_object,
            "RUBY_PLATFORM", self.newstr_fromstr(system.RUBY_PLATFORM))
        self.set_const(
            self.w_object,
            "RUBY_DESCRIPTION", self.newstr_fromstr(system.RUBY_DESCRIPTION))
        self.set_const(
            self.w_object,
            "RUBY_REVISION", self.newstr_fromstr(system.RUBY_REVISION))

    def load_kernel(self, kernel_path):
        self.send(
            self.w_kernel,
            "load",
            [self.newstr_fromstr(os.path.join(kernel_path, "bootstrap.rb"))]
        )

    @specialize.memo()
    def fromcache(self, key):
        return self.cache.getorbuild(key)

    # Methods for dealing with source code.

    def parse(self, source, initial_lineno=1, symtable=None):
        if symtable is None:
            symtable = SymbolTable()
        parser = Parser(Lexer(
            source, initial_lineno=initial_lineno, symtable=symtable))
        try:
            return parser.parse().getast()
        except ParsingError as e:
            source_pos = e.getsourcepos()
            token = e.message
            if source_pos is not None:
                msg = "line %d (unexpected %s)" % (source_pos.lineno, token)
            else:
                msg = ""
            raise self.error(self.w_SyntaxError, msg)
        except LexerError as e:
            raise self.error(
                self.w_SyntaxError, "line %d (%s)" % (e.pos.lineno, e.msg))

    def compile(self, source, filepath, initial_lineno=1, symtable=None):
        if symtable is None:
            symtable = SymbolTable()
        astnode = self.parse(
            source, initial_lineno=initial_lineno, symtable=symtable)
        ctx = CompilerContext(self, "<main>", symtable, filepath)
        with ctx.set_lineno(initial_lineno):
            try:
                astnode.compile(ctx)
            except CompilerError as e:
                raise self.error(self.w_SyntaxError, "%s" % e.msg)
        return ctx.create_bytecode(initial_lineno, [], [], None, None)

    def execute(self, source, w_self=None, lexical_scope=None, filepath="-e",
                initial_lineno=1):
        bc = self.compile(source, filepath, initial_lineno=initial_lineno)
        frame = self.create_frame(
            bc, w_self=w_self, lexical_scope=lexical_scope)
        with self.getexecutioncontext().visit_frame(frame):
            return self.execute_frame(frame, bc)

    @jit.loop_invariant
    def getexecutioncontext(self):
        ec = self._executioncontexts.get()
        if ec is None:
            ec = ExecutionContext()
            self._executioncontexts.set(ec)
        return ec

    def create_frame(self, bc, w_self=None, lexical_scope=None, block=None,
                     parent_interp=None, top_parent_interp=None,
                     regexp_match_cell=None):

        if w_self is None:
            w_self = self.w_top_self
        if regexp_match_cell is None:
            regexp_match_cell = ClosureCell(None)
        return Frame(
            jit.promote(bc), w_self, lexical_scope, block, parent_interp,
            top_parent_interp, regexp_match_cell
        )

    def execute_frame(self, frame, bc):
        return Interpreter().interpret(self, frame, bc)

    # Methods for allocating new objects.

    @signature(types.any(), types.bool(), returns=types.instance(W_Root))
    def newbool(self, boolvalue):
        if boolvalue:
            return self.w_true
        else:
            return self.w_false

    @signature(types.any(), types.int(),
               returns=types.instance(W_FixnumObject))
    def newint(self, intvalue):
        return W_FixnumObject(self, intvalue)

    def newbigint_fromint(self, intvalue):
        return W_BignumObject.newbigint_fromint(self, intvalue)

    def newbigint_fromfloat(self, floatvalue):
        return W_BignumObject.newbigint_fromfloat(self, floatvalue)

    def newbigint_fromrbigint(self, bigint):
        return W_BignumObject.newbigint_fromrbigint(self, bigint)

    @specialize.argtype(1)
    def newint_or_bigint(self, someinteger):
        if -sys.maxint <= someinteger <= sys.maxint:
            # The smallest int -sys.maxint - 1 has to be a Bignum,
            # because parsing gives a Bignum in that case
            return self.newint(intmask(someinteger))
        else:
            return self.newbigint_fromrbigint(
                rbigint.fromrarith_int(someinteger))

    @specialize.argtype(1)
    def newint_or_bigint_fromunsigned(self, someunsigned):
        # XXX somehow combine with above
        if 0 <= someunsigned <= sys.maxint:
            return self.newint(intmask(someunsigned))
        else:
            return self.newbigint_fromrbigint(
                rbigint.fromrarith_int(someunsigned))

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
        assert strvalue is not None
        return W_StringObject.newstr_fromstr(self, strvalue)

    def newstr_fromstrs(self, strs_w):
        return W_StringObject.newstr_fromstrs(self, strs_w)

    def newarray(self, items_w):
        return W_ArrayObject(self, items_w)

    def newhash(self):
        return W_HashObject(self)

    def newrange(self, w_start, w_end, exclusive):
        return W_RangeObject(self, w_start, w_end, exclusive)

    def newregexp(self, regexp, flags):
        return W_RegexpObject(self, regexp, flags)

    def newmodule(self, name, w_scope=None):
        complete_name = self.buildname(name, w_scope)
        return W_ModuleObject(self, complete_name)

    def newclass(self, name, superclass, is_singleton=False, w_scope=None,
                 attached=None):
        complete_name = self.buildname(name, w_scope)
        return W_ClassObject(
            self, complete_name, superclass,
            is_singleton=is_singleton, attached=attached)

    def newfunction(self, w_name, w_code, lexical_scope, visibility):
        name = self.symbol_w(w_name)
        assert isinstance(w_code, W_CodeObject)
        return W_UserFunction(name, w_code, lexical_scope, visibility)

    def newmethod(self, name, w_cls):
        w_function = w_cls.find_method(self, name)
        if w_function is None:
            raise self.error(
                self.w_NameError,
                "undefined method `%s' for class `%s'" % (
                    name, self.obj_to_s(w_cls)))
        else:
            return W_UnboundMethodObject(self, w_cls, w_function)

    def newproc(self, bytecode, w_self, lexical_scope, cells, block,
                parent_interp, top_parent_interp, regexp_match_cell,
                is_lambda=False):
        return W_ProcObject(
            self, bytecode, w_self, lexical_scope, cells, block, parent_interp,
            top_parent_interp, regexp_match_cell, is_lambda=False
        )

    @jit.unroll_safe
    def newbinding_fromframe(self, frame):
        names = frame.bytecode.cellvars + frame.bytecode.freevars
        cells = [None] * len(frame.cells)
        for i in xrange(len(frame.cells)):
            cells[i] = frame.cells[i].upgrade_to_closure(self, frame, i)
        return W_BindingObject(
            self, names, cells, frame.w_self, frame.lexical_scope)

    @jit.unroll_safe
    def newbinding_fromblock(self, block):
        names = block.bytecode.cellvars + block.bytecode.freevars
        cells = block.cells[:]
        return W_BindingObject(
            self, names, cells, block.w_self, block.lexical_scope)

    def buildname(self, name, w_scope):
        complete_name = name
        if w_scope is not None:
            assert isinstance(w_scope, W_ModuleObject)
            if w_scope is not self.w_object:
                complete_name = "%s::%s" % (self.obj_to_s(w_scope), name)
        return complete_name

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

    def str0_w(self, w_obj):
        string = w_obj.str_w(self)
        if "\x00" in string:
            raise self.error(self.w_ArgumentError, "string contains null byte")
        else:
            return string

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
        w_res = w_module.find_const(self, name, autoload=True)
        if w_res is None:
            w_res = self.send(
                w_module, "const_missing", [self.newsymbol(name)])
        return w_res

    @jit.elidable
    def _valid_const_name(self, name):
        if not name[0].isupper():
            return False
        for i in range(1, len(name)):
            ch = name[i]
            if not (ch.isalnum() or ch == "_" or ord(ch) > 127):
                return False
        return True

    def _check_const_name(self, name):
        if not self._valid_const_name(name):
            raise self.error(self.w_NameError, "wrong constant name %s" % name)

    def set_const(self, module, name, w_value):
        self._check_const_name(name)
        module.set_const(self, name, w_value)

    @jit.unroll_safe
    def _find_lexical_const(self, lexical_scope, name, autoload=True):
        w_res = None
        scope = lexical_scope
        # perform lexical search but skip Object
        while scope is not None:
            w_mod = scope.w_mod
            if w_mod is self.w_top_self:
                break
            w_res = w_mod.find_local_const(self, name, autoload=autoload)
            if w_res is not None:
                return w_res
            scope = scope.backscope

        object_seen = False
        fallback_scope = self.w_object

        if lexical_scope is not None:
            w_mod = lexical_scope.w_mod
            while w_mod is not None:
                object_seen = object_seen or w_mod is self.w_object
                # BasicObject was our starting point, do not use Object
                # as fallback
                if w_mod is self.w_basicobject and not object_seen:
                    fallback_scope = None
                w_res = w_mod.find_const(self, name, autoload=autoload)
                if w_res is not None:
                    return w_res
                if isinstance(w_mod, W_ClassObject):
                    w_mod = w_mod.superclass
                else:
                    break

        if fallback_scope is not None:
            w_res = fallback_scope.find_const(self, name, autoload=autoload)
        return w_res

    @jit.unroll_safe
    def find_lexical_const(self, lexical_scope, name):
        w_res = self._find_lexical_const(lexical_scope, name)
        if w_res is None:
            if lexical_scope is not None:
                w_mod = lexical_scope.w_mod
            else:
                w_mod = self.w_object
            w_res = self.send(w_mod, "const_missing", [self.newsymbol(name)])
        return w_res

    def find_instance_var(self, w_obj, name):
        w_res = w_obj.find_instance_var(self, name)
        return w_res if w_res is not None else self.w_nil

    def set_instance_var(self, w_obj, name, w_value):
        w_obj.set_instance_var(self, name, w_value)

    def find_class_var(self, w_module, name):
        w_res = w_module.find_class_var(self, name)
        if w_res is None:
            module_name = self.obj_to_s(w_module)
            raise self.error(
                self.w_NameError,
                "uninitialized class variable %s in %s" % (name, module_name))
        return w_res

    def set_class_var(self, w_module, name, w_value):
        w_module.set_class_var(self, name, w_value)

    def send(self, w_receiver, name, args_w=None, block=None):
        if args_w is None:
            args_w = []

        w_cls = self.getclass(w_receiver)
        raw_method = w_cls.find_method(self, name)
        return self._send_raw(
            name, raw_method, w_receiver, w_cls, args_w, block)

    def send_super(self, w_cls, w_receiver, name, args_w, block=None):
        raw_method = w_cls.find_method_super(self, name)
        return self._send_raw(
            name, raw_method, w_receiver, w_cls, args_w, block)

    def _send_raw(self, name, raw_method, w_receiver, w_cls, args_w, block):
        if raw_method is None:
            method_missing = w_cls.find_method(self, "method_missing")
            if method_missing is None:
                class_name = self.str_w(self.send(w_cls, "to_s"))
                raise self.error(
                    self.w_NoMethodError,
                    "undefined method `%s' for %s" % (name, class_name))
            else:
                args_w = [self.newsymbol(name)] + args_w
                return method_missing.call(self, w_receiver, args_w, block)
        return raw_method.call(self, w_receiver, args_w, block)

    def respond_to(self, w_receiver, name):
        w_cls = self.getclass(w_receiver)
        raw_method = w_cls.find_method(self, name)
        return raw_method is not None

    def is_kind_of(self, w_obj, w_cls):
        return w_obj.is_kind_of(self, w_cls)

    @jit.unroll_safe
    def invoke_block(self, block, args_w, block_arg=None):
        bc = block.bytecode
        frame = self.create_frame(
            bc, w_self=block.w_self, lexical_scope=block.lexical_scope,
            block=block.block, parent_interp=block.parent_interp,
            top_parent_interp=block.top_parent_interp,
            regexp_match_cell=block.regexp_match_cell,
        )
        if block.is_lambda:
            frame.handle_args(self, bc, args_w, block_arg)
        else:
            if (len(bc.arg_pos) != 0 or bc.splat_arg_pos != -1 or
                    bc.block_arg_pos != -1):
                frame.handle_block_args(self, bc, args_w, block_arg)
        assert len(block.cells) == len(bc.freevars)
        for i in xrange(len(bc.freevars)):
            frame.cells[len(bc.cellvars) + i] = block.cells[i]

        with self.getexecutioncontext().visit_frame(frame):
            return self.execute_frame(frame, bc)

    def invoke_function(self, w_function, w_receiver, args_w, block):
        return self._send_raw(
            w_function.name, w_function, w_receiver, self.getclass(w_receiver),
            args_w, block)

    def error(self, w_type, msg="", optargs=None):
        if not optargs:
            optargs = []
        args_w = [self.newstr_fromstr(msg)] + optargs
        w_exc = self.send(w_type, "new", args_w)
        assert isinstance(w_exc, W_ExceptionObject)
        return RubyError(w_exc)

    def hash_w(self, w_obj):
        return self.int_w(self.send(w_obj, "hash"))

    def eq_w(self, w_obj1, w_obj2):
        return self.is_true(self.send(w_obj2, "eql?", [w_obj1]))

    def register_exit_handler(self, w_proc):
        self.exit_handlers_w.append(w_proc)

    def run_exit_handlers(self):
        status = -1
        while self.exit_handlers_w:
            w_proc = self.exit_handlers_w.pop()
            try:
                self.send(w_proc, "call")
            except RubyError as e:
                w_exc = e.w_value
                if isinstance(w_exc, W_SystemExit):
                    status = w_exc.status
                else:
                    print_traceback(self, e.w_value)
        return status

    def subscript_access(self, length, w_idx, w_count):
        inclusive = False
        as_range = False
        end = 0
        nil = False

        if isinstance(w_idx, W_RangeObject) and not w_count:
            start = self.int_w(self.convert_type(
                w_idx.w_start, self.w_fixnum, "to_int"))
            end = self.int_w(self.convert_type(
                w_idx.w_end, self.w_fixnum, "to_int"))
            inclusive = not w_idx.exclusive
            as_range = True
        else:
            start = self.int_w(self.convert_type(
                w_idx, self.w_fixnum, "to_int"))
            if w_count:
                end = self.int_w(self.convert_type(
                    w_count, self.w_fixnum, "to_int"))
                if end >= 0:
                    as_range = True
                else:
                    if start < 0:
                        start += length
                    return (start, end, False, True)

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
            nil = start < 0 or end < 0 or start > length
        else:
            nil = start < 0 or start >= length

        return (start, end, as_range, nil)

    def convert_type(self, w_obj, w_cls, method, raise_error=True,
                     reraise_error=False):
        if self.is_kind_of(w_obj, w_cls):
            return w_obj

        try:
            w_res = self.send(w_obj, method)
        except RubyError as e:
            if reraise_error:
                raise e
            self.mark_topframe_not_escaped()
            if not raise_error:
                return self.w_nil
            src_cls_name = self.obj_to_s(self.getclass(w_obj))
            w_cls_name = self.obj_to_s(w_cls)
            raise self.error(
                self.w_TypeError,
                "can't convert %s into %s" % (src_cls_name, w_cls_name))

        if not w_res or w_res is self.w_nil and not raise_error:
            return self.w_nil
        elif not self.is_kind_of(w_res, w_cls):
            src_cls = self.obj_to_s(self.getclass(w_obj))
            res_cls = self.obj_to_s(self.getclass(w_res))
            w_cls_name = self.obj_to_s(w_cls)
            raise self.error(
                self.w_TypeError,
                "can't convert %s to %s (%s#%s gives %s)" % (
                    src_cls, w_cls_name, src_cls, method, res_cls))
        else:
            return w_res

    def mark_topframe_not_escaped(self):
        self.getexecutioncontext().gettopframe().escaped = False

    def infect(self, w_dest, w_src, taint=True, untrust=True, freeze=False):
        """
        By default copies tainted and untrusted state from src to dest.
        Frozen state isn't copied by default, as this is the rarer case MRI.
        """
        if taint and self.is_true(w_src.get_flag(self, "tainted?")):
            w_dest.set_flag(self, "tainted?")
        if untrust and self.is_true(w_src.get_flag(self, "untrusted?")):
            w_dest.set_flag(self, "untrusted?")
        if freeze and self.is_true(w_src.get_flag(self, "frozen?")):
            w_dest.set_flag(self, "frozen?")

    def getaddrstring(self, w_obj):
        w_id = self.newint_or_bigint(compute_unique_id(w_obj))
        w_4 = self.newint(4)
        w_0x0F = self.newint(0x0F)
        i = 2 * rffi.sizeof(llmemory.Address)
        addrstring = [" "] * i
        while True:
            n = self.int_w(self.send(w_id, "&", [w_0x0F]))
            n += ord("0")
            if n > ord("9"):
                n += (ord("a") - ord("9") - 1)
            i -= 1
            addrstring[i] = chr(n)
            if i == 0:
                break
            w_id = self.send(w_id, ">>", [w_4])
        return "".join(addrstring)

    def any_to_s(self, w_obj):
        return "#<%s:0x%s>" % (
            self.obj_to_s(self.getnonsingletonclass(w_obj)),
            self.getaddrstring(w_obj)
        )

    def obj_to_s(self, w_obj):
        return self.str_w(self.send(w_obj, "to_s"))

    def compare(self, w_a, w_b, block=None):
        if block is None:
            w_cmp_res = self.send(w_a, "<=>", [w_b])
        else:
            w_cmp_res = self.invoke_block(block, [w_a, w_b])
        if w_cmp_res is self.w_nil:
            raise self.error(
                self.w_ArgumentError,
                "comparison of %s with %s failed" % (
                    self.obj_to_s(self.getclass(w_a)),
                    self.obj_to_s(self.getclass(w_b)),
                )
            )
        else:
            return w_cmp_res
