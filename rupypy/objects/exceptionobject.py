from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object, W_BuiltinObject


def new_exception_allocate(classdef):
    @classdef.singleton_method("allocate", msg="str")
    def method_allocate(self, space, msg):
        return classdef.cls(space, msg)

class W_ExceptionObject(W_BuiltinObject):
    classdef = ClassDef("Exception", W_Object.classdef)

    def __init__(self, space, msg):
        W_BuiltinObject.__init__(self, space)
        self.msg = msg
        self.frame = None
        self.last_instructions = []

    method_allocate = new_exception_allocate(classdef)

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.msg)


class W_ScriptError(W_ExceptionObject):
    classdef = ClassDef("ScriptError", W_ExceptionObject.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_LoadError(W_ScriptError):
    classdef = ClassDef("LoadError", W_ScriptError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_StandardError(W_ExceptionObject):
    classdef = ClassDef("StandardError", W_ExceptionObject.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_TypeError(W_ExceptionObject):
    classdef = ClassDef("TypeError", W_StandardError.classdef)
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


class W_SyntaxError(W_ScriptError):
    classdef = ClassDef("SyntaxError", W_ScriptError.classdef)
    method_allocate = new_exception_allocate(classdef)
