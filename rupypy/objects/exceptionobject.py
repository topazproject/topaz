from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


def new_exception_allocate(classdef):
    @classdef.singleton_method("allocate", msg="str")
    def method_allocate(self, space, msg="str"):
        return classdef.cls(space, msg)


class W_ExceptionObject(W_Object):
    classdef = ClassDef("Exception", W_Object.classdef)

    def __init__(self, space, msg):
        W_Object.__init__(self, space)
        self.msg = msg
        self.frame = None
        self.last_instructions = []

    method_allocate = new_exception_allocate(classdef)

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.msg)

    @classdef.singleton_method("exception")
    def singleton_method_exception(self, space, args_w):
        return space.send(self, space.newsymbol("new"), args_w)

    @classdef.method("exception")
    def method_exception(self, space, w_string=None):
        if w_string is None:
            return self
        else:
            return space.send(space.getclassfor(self.__class__), space.newsymbol("new"), [w_string])

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


class W_ArgumentError(W_StandardError):
    classdef = ClassDef("ArgumentError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)
