from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


def new_exception_allocate(classdef):
    @classdef.singleton_method("allocate", msg=str)
    def method_allocate(self, space, msg):
        return classdef.cls(msg)

class W_ExceptionObject(W_BaseObject):
    classdef = ClassDef("Exception", W_BaseObject.classdef)

    def __init__(self, msg):
        self.msg = msg

    method_allocate = new_exception_allocate(classdef)

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.msg)

class W_StandardError(W_ExceptionObject):
    classdef = ClassDef("StandardError", W_ExceptionObject.classdef)
    method_allocate = new_exception_allocate(classdef)

class W_NameError(W_StandardError):
    classdef = ClassDef("NameError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)

class W_NoMethodError(W_NameError):
    classdef = ClassDef("NoMethodError", W_NameError.classdef)
    method_allocate = new_exception_allocate(classdef)

class W_ZeroDivisionError(W_StandardError):
    classdef = ClassDef("ZeroDivisionError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)

class W_ScriptError(W_ExceptionObject):
    classdef = ClassDef("ScriptError", W_ExceptionObject.classdef)
    method_allocate = new_exception_allocate(classdef)

class W_SyntaxError(W_ScriptError):
    classdef = ClassDef("SyntaxError", W_ScriptError.classdef)
    method_allocate = new_exception_allocate(classdef)