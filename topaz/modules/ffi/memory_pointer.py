from topaz.modules.ffi.pointer import W_PointerObject
from topaz.module import ClassDef

from rpython.rtyper.lltypesystem import rffi

class W_MemoryPointerObject(W_PointerObject):
    classdef = ClassDef('MemoryPointer', W_PointerObject.classdef)
