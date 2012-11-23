from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object
from rupypy.utils import re_compile


class W_RegexpObject(W_Object):
    classdef = ClassDef("Regexp", W_Object.classdef)

    def __init__(self, space, regexp):
        W_Object.__init__(self, space)
        self.set_regexp(regexp)

    def _check_initialized(self, space):
        if self.regexp is None:
            raise space.error(space.w_TypeError, "uninitialized Regexp")

    def set_regexp(self, regexp):
        if regexp is not None:
            self.regexp = regexp
            code, flags, groupindex, indexgroup = re_compile.compile(regexp, 0)
            self.code = code
            self.flags = flags
            self.groupindex = groupindex
            self.indexgroup = indexgroup

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_RegexpObject(space, None)

    @classdef.singleton_method("compile")
    def method_compile(self, space, args_w):
        return space.send(self, space.newsymbol("new"), args_w)

    @classdef.method("initialize", source="str")
    def method_initialize(self, space, source):
        self.set_regexp(source)

    @classdef.method("==")
    def method_equal(self, space, w_other):
        if self is w_other:
            return space.w_true
        if not isinstance(w_other, W_RegexpObject):
            return space.w_false
        self._check_initialized(space)
        w_other._check_initialized(space)
        return space.newbool(self.regexp == w_other.regexp)

    @classdef.method("source")
    def method_source(self, space):
        self._check_initialized(space)
        return space.newstr_fromstr(self.regexp)
