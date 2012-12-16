from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


def new_exception_allocate(classdef):
    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return classdef.cls(space, self)


class W_ExceptionObject(W_Object):
    _attrs_ = ["msg", "frame", "last_instructions"]

    classdef = ClassDef("Exception", W_Object.classdef, filepath=__file__)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.msg = ""
        self.frame = None

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.msg)

    method_allocate = new_exception_allocate(classdef)

    @classdef.method("initialize")
    def method_initialize(self, space, w_msg=None):
        if w_msg is space.w_nil or w_msg is None:
            msg = space.getclass(self).name
        else:
            msg = space.str_w(w_msg)
        self.msg = msg

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

    @classdef.method("message")
    def method_message(self, space):
        return space.newstr_fromstr(self.msg)

    @classdef.method("backtrace")
    def method_backtrace(self, space):
        frame = self.frame
        results_w = []
        prev_frame = None
        while frame is not None and frame.has_contents():
            results_w.append(space.newstr_fromstr("%s:%d:in `%s'" % (
                frame.get_filename(),
                frame.get_lineno(prev_frame),
                frame.get_code_name(),
            )))
            prev_frame = frame
            frame = frame.backref()
        return space.newarray(results_w)


class W_ScriptError(W_ExceptionObject):
    classdef = ClassDef("ScriptError", W_ExceptionObject.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_LoadError(W_ScriptError):
    classdef = ClassDef("LoadError", W_ScriptError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_StandardError(W_ExceptionObject):
    classdef = ClassDef("StandardError", W_ExceptionObject.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_SystemExit(W_ExceptionObject):
    classdef = ClassDef("SystemExit", W_ExceptionObject.classdef, filepath=__file__)

    def __init__(self, space, klass=None):
        W_ExceptionObject.__init__(self, space, klass)
        self.status = 0

    method_allocate = new_exception_allocate(classdef)

    @classdef.method("initialize", status="int")
    def method_initialize(self, space, w_msg=None, status=0):
        W_ExceptionObject.method_initialize(self, space, w_msg)
        self.status = status

    @classdef.method("success?")
    def method_successp(self, space):
        return space.newbool(self.status == 0)

    @classdef.method("status")
    def method_status(self, space):
        return space.newint(self.status)


class W_TypeError(W_ExceptionObject):
    classdef = ClassDef("TypeError", W_StandardError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_NameError(W_StandardError):
    classdef = ClassDef("NameError", W_StandardError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_NoMethodError(W_NameError):
    classdef = ClassDef("NoMethodError", W_NameError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_ZeroDivisionError(W_StandardError):
    classdef = ClassDef("ZeroDivisionError", W_StandardError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_SyntaxError(W_ScriptError):
    classdef = ClassDef("SyntaxError", W_ScriptError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_NotImplementedError(W_ScriptError):
    classdef = ClassDef("NotImplementedError", W_ScriptError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_ArgumentError(W_StandardError):
    classdef = ClassDef("ArgumentError", W_StandardError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_RangeError(W_StandardError):
    classdef = ClassDef("RangeError", W_StandardError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_RuntimeError(W_StandardError):
    classdef = ClassDef("RuntimeError", W_StandardError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_SystemCallError(W_StandardError):
    classdef = ClassDef("SystemCallError", W_StandardError.classdef, filepath=__file__)

    def __init__(self, space, klass=None):
        W_ExceptionObject.__init__(self, space, klass)
        self.errno = 0

    method_allocate = new_exception_allocate(classdef)

    @classdef.method("initialize", errno="int")
    def method_initialize(self, space, w_msg=None, errno=0):
        W_StandardError.method_initialize(self, space, w_msg)
        self.errno = errno

    @classdef.method("errno")
    def method_status(self, space):
        return space.newint(self.errno)


class W_IndexError(W_StandardError):
    classdef = ClassDef("IndexError", W_StandardError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_StopIteration(W_IndexError):
    classdef = ClassDef("StopIteration", W_IndexError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)


class W_LocalJumpError(W_StandardError):
    classdef = ClassDef("LocalJumpError", W_StandardError.classdef, filepath=__file__)
    method_allocate = new_exception_allocate(classdef)
