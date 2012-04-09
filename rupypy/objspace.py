from rupypy.bytecode import CompilerContext
from rupypy.objects.boolobject import W_TrueObject
from rupypy.objects.intobject import W_IntObject
from rupypy.objects.symbolobject import W_SymbolObject
from rupypy.parser import Transformer, _parse


class ObjectSpace(object):
    def __init__(self):
        self.transformer = Transformer()

    def parse(self, source):
        return self.transformer.visit_main(_parse(source))

    def compile(self, source):
        astnode = self.parse(source)
        c = CompilerContext(self)
        astnode.compile(c)
        return c.create_bytecode()

    def newbool(self, boolvalue):
        if boolvalue:
            return W_TrueObject()
        else:
            return W_FalseObject()

    def newint(self, intvalue):
        return W_IntObject(intvalue)

    def newsymbol(self, symbol):
        return W_SymbolObject(symbol)