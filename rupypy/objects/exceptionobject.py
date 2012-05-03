from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_ExceptionObject(W_BaseObject):
    classdef = ClassDef("Exception", W_BaseObject.classdef)

class W_StandardError(W_ExceptionObject):
    classdef = ClassDef("StandardError", W_ExceptionObject.classdef)

class W_ZeroDivisionError(W_StandardError):
    classdef = ClassDef("ZeroDivisionError", W_StandardError.classdef)