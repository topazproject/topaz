from pypy.rlib.rsre import rsre_core

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object
from rupypy.utils import re_compile


class W_RegexpObject(W_Object):
    classdef = ClassDef("Regexp", W_Object.classdef)

    def __init__(self, space, regexp):
        W_Object.__init__(self, space)
        self.set_regexp(regexp)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.globals.define_virtual("$~",
            cls._get_regexp_cell,
            cls._set_regexp_cell,
        )
        space.globals.define_virtual("$1", cls.create_regexp_match_getter(1))
        space.globals.define_virtual("$2", cls.create_regexp_match_getter(2))
        space.globals.define_virtual("$3", cls.create_regexp_match_getter(3))
        space.globals.define_virtual("$4", cls.create_regexp_match_getter(4))
        space.globals.define_virtual("$5", cls.create_regexp_match_getter(5))
        space.globals.define_virtual("$6", cls.create_regexp_match_getter(6))
        space.globals.define_virtual("$7", cls.create_regexp_match_getter(7))
        space.globals.define_virtual("$8", cls.create_regexp_match_getter(8))
        space.globals.define_virtual("$9", cls.create_regexp_match_getter(9))

    @staticmethod
    def _get_regexp_cell(space):
        return space.getexecutioncontext().regexp_match_cell.get(None, 0)

    @staticmethod
    def _set_regexp_cell(space, w_match):
        if not space.is_kind_of(w_match, space.getclassfor(W_MatchDataObject)):
            raise space.error(space.w_TypeError, "wrong argument type %s (expected MatchData)" % space.getclass(w_match).name)
        space.getexecutioncontext().regexp_match_cell.set(None, 0, w_match)

    @staticmethod
    def create_regexp_match_getter(n):
        def getter(space):
            w_match = space.getexecutioncontext().regexp_match_cell.get(None, 0)
            if w_match is None:
                return space.w_nil
            else:
                return space.send(w_match, space.newsymbol("[]"), [space.newint(n)])
        return getter

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

    def make_ctx(self, s):
        pos = 0
        endpos = len(s)
        return rsre_core.StrMatchContext(self.code, s, pos, endpos, self.flags)

    def get_match_result(self, space, ctx, found):
        if found:
            w_match = W_MatchDataObject(space, self, ctx)
        else:
            w_match = space.w_nil
        space.globals.set(space, "$~", w_match)
        return w_match

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

    @classdef.method("=~", s="str")
    def method_match(self, space, s):
        ctx = self.make_ctx(s)
        matched = rsre_core.search_context(ctx)
        self.get_match_result(space, ctx, matched)
        if matched:
            return space.newint(ctx.match_start)
        else:
            return space.w_nil


class W_MatchDataObject(W_Object):
    classdef = ClassDef("MatchData", W_Object.classdef)

    def __init__(self, space, regexp, ctx):
        W_Object.__init__(self, space)
        self.regexp = regexp
        self.ctx = ctx
        self._flatten_cache = None

    def flatten_marks(self):
        if self._flatten_cache is None:
            self._flatten_cache = self._build_flattened_marks(self.ctx, len(self.regexp.indexgroup))
        return self._flatten_cache

    def _build_flattened_marks(self, ctx, num_groups):
        if num_groups == 0:
            return None
        result = [-1] * (2 * num_groups)
        mark = ctx.match_marks
        while mark is not None:
            index = mark.gid
            if result[index] == -1:
                result[index] = mark.position
            mark = mark.prev
        return result

    def get_span(self, n):
        fmarks = self.flatten_marks()
        idx = 2 * (n - 1)
        assert idx >= 0
        return fmarks[idx], fmarks[idx + 1]

    @classdef.method("[]", n="int")
    def method_subscript(self, space, n):
        if 1 <= n <= len(self.regexp.indexgroup):
            start, end = self.get_span(n)
            return space.newstr_fromstr(self.ctx._string[start:end])
        else:
            return space.w_nil
