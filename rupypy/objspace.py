from pypy.rlib.objectmodel import specialize
from pypy.tool.cache import Cache

from rupypy.bytecode import CompilerContext
from rupypy.interpreter import Interpreter, Frame
from rupypy.module import ClassCache
from rupypy.objects.boolobject import W_TrueObject, W_FalseObject
from rupypy.objects.classobject import W_ClassObject
from rupypy.objects.intobject import W_IntObject
from rupypy.objects.nilobject import W_NilObject
from rupypy.objects.objectobject import W_Object
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.symbolobject import W_SymbolObject
from rupypy.parser import Transformer, _parse


class SpaceCache(Cache):
    def __init__(self, space):
        Cache.__init__(self)
        self.space = space

    def _build(self, obj):
        return obj(self.space)

class ObjectSpace(object):
    def __init__(self):
        self.transformer = Transformer()
        self.w_top_self = W_Object()
        self.cache = SpaceCache(self)

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
        return self.transformer.visit_main(_parse(source))

    def compile(self, source):
        astnode = self.parse(source)
        c = CompilerContext(self)
        astnode.compile(c)
        return c.create_bytecode()

    def execute(self, source):
        bc = self.compile(source)
        return Interpreter().interpret(self, Frame(bc, self.w_top_self), bc)

    # Methods for allocating new objects.

    def newint(self, intvalue):
        return W_IntObject(intvalue)

    def newsymbol(self, symbol):
        return W_SymbolObject(symbol)

    def newstr(self, chars):
        return W_StringObject(chars)

    def newclass(self, name):
        return W_ClassObject(name)


    def int_w(self, w_obj):
        return w_obj.int_w(self)

    def symbol_w(self, w_obj):
        return w_obj.symbol_w(self)

    def str_w(self, w_obj):
        return w_obj.str_w(self)

    # Methods for implementing the language semantics.

    def is_true(self, w_obj):
        return w_obj.is_true(self)

    def getclass(self, w_receiver):
        return w_receiver.getclass(self)

    def getclassobject(self, classdef):
        return self.fromcache(ClassCache).getorbuild(classdef)

    def send(self, w_receiver, w_method, args_w=None):
        if args_w is None:
            args_w = []
        w_cls = self.getclass(w_receiver)
        raw_method = w_cls.find_method(self, self.symbol_w(w_method))
        return raw_method(w_receiver, self, args_w)