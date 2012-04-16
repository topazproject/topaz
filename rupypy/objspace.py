from pypy.rlib.objectmodel import specialize
from pypy.tool.cache import Cache

from rupypy.bytecode import CompilerContext
from rupypy.interpreter import Interpreter, Frame
from rupypy.module import ClassCache, Function
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.boolobject import W_TrueObject, W_FalseObject
from rupypy.objects.classobject import W_ClassObject
from rupypy.objects.codeobject import W_CodeObject
from rupypy.objects.intobject import W_IntObject
from rupypy.objects.nilobject import W_NilObject
from rupypy.objects.objectobject import W_Object
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

    def _freeze_(self):
        return True

    @specialize.memo()
    def fromcache(self, key):
        return self.cache.getorbuild(key)

    # Methods for dealing with source code.

    def parse(self, source):
        return self.transformer.visit_main(to_ast().transform(_parse(source)))

    def compile(self, source):
        astnode = self.parse(source)
        c = CompilerContext(self)
        astnode.compile(c)
        return c.create_bytecode()

    def execute(self, source, w_self=None):
        bc = self.compile(source)
        if w_self is None:
            w_self = self.w_top_self
        frame = Frame(bc, w_self, self.getclassfor(W_Object))
        return Interpreter().interpret(self, frame, bc)

    # Methods for allocating new objects.

    def newbool(self, boolvalue):
        if boolvalue:
            return self.w_true
        else:
            return self.w_false

    def newint(self, intvalue):
        return W_IntObject(intvalue)

    def newsymbol(self, symbol):
        return W_SymbolObject(symbol)

    def newstr_fromchars(self, chars):
        return W_StringObject.newstr_fromchars(self, chars)

    def newstr_fromstr(self, strvalue):
        return W_StringObject.newstr_fromstr(self, strvalue)

    def newarray(self, items_w):
        return W_ArrayObject(items_w)

    def newclass(self, name, superclass):
        return W_ClassObject(name, superclass)

    def newcode(self, bytecode):
        return W_CodeObject(bytecode)

    def newfunction(self, w_name, w_code):
        name = self.symbol_w(w_name)
        assert isinstance(w_code, W_CodeObject)
        bytecode = w_code.bytecode
        return Function(name, bytecode)

    def int_w(self, w_obj):
        return w_obj.int_w(self)

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

    def invoke_block(self, block, *args_w):
        bc = block.bytecode
        frame = Frame(bc, self.w_top_self, self.getclassfor(W_Object))
        # XXX arg count checking
        for i, w_arg in enumerate(args_w):
            frame.locals_w[i] = w_arg
        return Interpreter().interpret(self, frame, bc)
