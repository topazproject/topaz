from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


def new_exception_allocate(classdef):
    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return classdef.cls(space, self)


class W_ExceptionObject(W_Object):
    _attrs_ = ["msg", "frame", "last_instructions", "w_backtrace"]

    classdef = ClassDef("Exception", W_Object.classdef)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.msg = ""
        self.frame = None
        self.w_backtrace = None

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.msg)

    method_allocate = new_exception_allocate(classdef)

    def copy_instance_vars(self, space, w_other):
        """Copies special instance vars after #copy or #dup"""
        assert isinstance(w_other, W_ExceptionObject)
        W_Object.copy_instance_vars(self, space, w_other)
        self.msg = w_other.msg
        self.frame = w_other.frame
        self.w_backtrace = w_other.w_backtrace

    @classdef.method("initialize")
    def method_initialize(self, space, w_msg=None):
        if w_msg is space.w_nil or w_msg is None:
            msg = space.getclass(self).name
        else:
            msg = space.str_w(space.send(w_msg, "to_s"))
        self.msg = msg

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.msg)

    @classdef.singleton_method("exception")
    def singleton_method_exception(self, space, args_w):
        return space.send(self, "new", args_w)

    @classdef.method("exception")
    def method_exception(self, space, w_string=None):
        if w_string is None:
            return self
        else:
            return space.send(space.getclassfor(self.__class__), "new", [w_string])

    @classdef.method("message")
    def method_message(self, space):
        return space.send(self, "to_s")

    @classdef.method("backtrace")
    def method_backtrace(self, space):
        if self.w_backtrace is not None:
            return self.w_backtrace
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

    @classdef.method("set_backtrace")
    def method_set_backtrace(self, space, w_backtrace):
        if w_backtrace is space.w_nil:
            self.w_backtrace = w_backtrace
            return w_backtrace
        if space.is_kind_of(w_backtrace, space.w_array):
            for w_obj in space.listview(w_backtrace):
                if not space.is_kind_of(w_obj, space.w_string):
                    raise space.error(space.w_TypeError, "backtrace must be Array of String")
            self.w_backtrace = w_backtrace
            return w_backtrace
        if space.is_kind_of(w_backtrace, space.w_string):
            self.w_backtrace = space.newarray([w_backtrace])
            return self.w_backtrace
        raise space.error(space.w_TypeError, "backtrace must be Array of String")

    @classdef.method("==")
    def method_eq(self, space, w_other):
        if not isinstance(w_other, W_ExceptionObject):
            return space.w_false
        if self is w_other:
            return space.w_true

        w_msg = space.send(self, "message")
        w_backtrace = space.send(self, "backtrace")
        return space.newbool(
            space.is_true(space.send(w_msg, "==", [space.send(w_other, "message")])) and
            space.is_true(space.send(w_backtrace, "==", [space.send(w_other, "backtrace")]))
        )


class W_ScriptError(W_ExceptionObject):
    classdef = ClassDef("ScriptError", W_ExceptionObject.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_LoadError(W_ScriptError):
    classdef = ClassDef("LoadError", W_ScriptError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_StandardError(W_ExceptionObject):
    classdef = ClassDef("StandardError", W_ExceptionObject.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_SystemStackError(W_ExceptionObject):
    classdef = ClassDef("SystemStackError", W_ExceptionObject.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_SystemExit(W_ExceptionObject):
    classdef = ClassDef("SystemExit", W_ExceptionObject.classdef)

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
    classdef = ClassDef("TypeError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_NameError(W_StandardError):
    classdef = ClassDef("NameError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)

    @classdef.method("initialize")
    def method_initialize(self, space, w_msg=None, w_name=None):
        W_ExceptionObject.method_initialize(self, space, w_msg)
        self.w_name = w_name or space.w_nil

    @classdef.method("name")
    def method_name(self, space):
        return self.w_name


class W_NoMethodError(W_NameError):
    classdef = ClassDef("NoMethodError", W_NameError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_ZeroDivisionError(W_StandardError):
    classdef = ClassDef("ZeroDivisionError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_SyntaxError(W_ScriptError):
    classdef = ClassDef("SyntaxError", W_ScriptError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_NotImplementedError(W_ScriptError):
    classdef = ClassDef("NotImplementedError", W_ScriptError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_ArgumentError(W_StandardError):
    classdef = ClassDef("ArgumentError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_RangeError(W_StandardError):
    classdef = ClassDef("RangeError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_FloatDomainError(W_RangeError):
    classdef = ClassDef("FloatDomainError", W_RangeError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_RuntimeError(W_StandardError):
    classdef = ClassDef("RuntimeError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_SystemCallError(W_StandardError):
    classdef = ClassDef("SystemCallError", W_StandardError.classdef)

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
    classdef = ClassDef("IndexError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_KeyError(W_IndexError):
    classdef = ClassDef("KeyError", W_IndexError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_StopIteration(W_IndexError):
    classdef = ClassDef("StopIteration", W_IndexError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_LocalJumpError(W_StandardError):
    classdef = ClassDef("LocalJumpError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_IOError(W_StandardError):
    classdef = ClassDef("IOError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_EOFError(W_IOError):
    classdef = ClassDef("EOFError", W_IOError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_RegexpError(W_StandardError):
    classdef = ClassDef("RegexpError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_ThreadError(W_StandardError):
    classdef = ClassDef("ThreadError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)


class W_FiberError(W_StandardError):
    classdef = ClassDef("FiberError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)
