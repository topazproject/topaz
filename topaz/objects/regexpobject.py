from rpython.rlib.rsre import rsre_core

from topaz.coerce import Coerce
from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.utils import regexp


RE_ESCAPE_TABLE = [chr(i) for i in xrange(256)]
RE_ESCAPE_TABLE[ord("\t")] = "\\t"
RE_ESCAPE_TABLE[ord("\n")] = "\\n"
RE_ESCAPE_TABLE[ord("\v")] = "\\v"
RE_ESCAPE_TABLE[ord("\f")] = "\\f"
RE_ESCAPE_TABLE[ord("\r")] = "\\r"
RE_ESCAPE_TABLE[ord(" ")] = "\\ "
RE_ESCAPE_TABLE[ord("#")] = "\\#"
RE_ESCAPE_TABLE[ord("$")] = "\\$"
RE_ESCAPE_TABLE[ord("(")] = "\\("
RE_ESCAPE_TABLE[ord(")")] = "\\)"
RE_ESCAPE_TABLE[ord("*")] = "\\*"
RE_ESCAPE_TABLE[ord("+")] = "\\+"
RE_ESCAPE_TABLE[ord("-")] = "\\-"
RE_ESCAPE_TABLE[ord(".")] = "\\."
RE_ESCAPE_TABLE[ord("?")] = "\\?"
RE_ESCAPE_TABLE[ord("[")] = "\\["
RE_ESCAPE_TABLE[ord("\\")] = "\\\\"
RE_ESCAPE_TABLE[ord("]")] = "\\]"
RE_ESCAPE_TABLE[ord("^")] = "\\^"
RE_ESCAPE_TABLE[ord("{")] = "\\{"
RE_ESCAPE_TABLE[ord("|")] = "\\|"
RE_ESCAPE_TABLE[ord("}")] = "\\}"


class RegexpCache(object):
    # TODO: this should use an LRU cache, and be elidable for the JIT.
    def __init__(self, space):
        self._contents = {}

    def contains(self, pattern, flags):
        return (pattern, flags) in self._contents

    def get(self, pattern, flags):
        return self._contents[pattern, flags]

    def set(self, pattern, flags, compiled_regexp):
        self._contents[pattern, flags] = compiled_regexp


class W_RegexpObject(W_Object):
    classdef = ClassDef("Regexp", W_Object.classdef)

    def __init__(self, space, source, flags):
        W_Object.__init__(self, space)
        self.set_source(space, source, flags)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.globals.define_virtual("$~",
            cls._get_regexp_match,
            cls._set_regexp_match,
        )
        space.globals.define_virtual("$1", cls._create_regexp_match_getter(1))
        space.globals.define_virtual("$2", cls._create_regexp_match_getter(2))
        space.globals.define_virtual("$3", cls._create_regexp_match_getter(3))
        space.globals.define_virtual("$4", cls._create_regexp_match_getter(4))
        space.globals.define_virtual("$5", cls._create_regexp_match_getter(5))
        space.globals.define_virtual("$6", cls._create_regexp_match_getter(6))
        space.globals.define_virtual("$7", cls._create_regexp_match_getter(7))
        space.globals.define_virtual("$8", cls._create_regexp_match_getter(8))
        space.globals.define_virtual("$9", cls._create_regexp_match_getter(9))
        space.globals.define_virtual("$&", cls._create_regexp_match_getter(0))
        space.globals.define_virtual("$+", cls._get_last_match)
        space.globals.define_virtual("$`", cls._get_pre_match)
        space.globals.define_virtual("$'", cls._get_post_match)
        space.set_const(w_cls, "IGNORECASE", space.newint(regexp.IGNORE_CASE))
        space.set_const(w_cls, "EXTENDED", space.newint(regexp.EXTENDED))
        space.set_const(w_cls, "MULTILINE", space.newint(regexp.DOT_ALL))
        space.set_const(w_cls, "FIXEDENCODING", space.newint(regexp.FIXED_ENCODING))
        space.set_const(w_cls, "NOENCODING", space.newint(regexp.NO_ENCODING))

    @staticmethod
    def _get_regexp_cell(space):
        return space.getexecutioncontext().gettoprubyframe().regexp_match_cell

    @staticmethod
    def _get_regexp_match(space):
        return W_RegexpObject._get_regexp_cell(space).get(space, None, 0)

    @staticmethod
    def _set_regexp_match(space, w_match):
        if (w_match is not space.w_nil and
            not space.is_kind_of(w_match, space.getclassfor(W_MatchDataObject))):
            raise space.error(space.w_TypeError, "wrong argument type %s (expected MatchData)" % space.getclass(w_match).name)
        W_RegexpObject._get_regexp_cell(space).set(space, None, 0, w_match)

    @staticmethod
    def _create_regexp_match_getter(n):
        def getter(space):
            w_match = W_RegexpObject._get_regexp_match(space)
            if w_match is None:
                return space.w_nil
            else:
                return space.send(w_match, "[]", [space.newint(n)])
        return getter

    @staticmethod
    def _get_last_match(space):
        w_match = W_RegexpObject._get_regexp_match(space)
        if w_match is None:
            return space.w_nil
        else:
            w_size = space.send(w_match, "size")
            w_last = space.send(w_size, "-", [space.newint(1)])
            return space.send(w_match, "[]", [w_last])

    @staticmethod
    def _get_pre_match(space):
        w_match = W_RegexpObject._get_regexp_match(space)
        if w_match is None:
            return space.w_nil
        else:
            return space.send(w_match, "pre_match")

    @staticmethod
    def _get_post_match(space):
        w_match = W_RegexpObject._get_regexp_match(space)
        if w_match is None:
            return space.w_nil
        else:
            return space.send(w_match, "post_match")

    def _check_initialized(self, space):
        if self.source is None:
            raise space.error(space.w_TypeError, "uninitialized Regexp")

    def set_source(self, space, source, flags):
        if source is not None:
            cache = space.fromcache(RegexpCache)
            self.source = source
            code, flags, groupcount, groupindex, indexgroup, group_offsets = regexp.compile(cache, source, flags)
            self.code = code
            self.flags = flags
            self.groupcount = groupcount
            self.groupindex = groupindex
            self.indexgroup = indexgroup
            self.group_offsets = group_offsets

    def make_ctx(self, s, offset=0):
        assert offset >= 0
        endpos = len(s)
        return rsre_core.StrMatchContext(self.code, s, offset, endpos, self.flags)

    def get_match_result(self, space, ctx, target, found):
        if found:
            w_match = W_MatchDataObject(space, self, ctx, target)
        else:
            w_match = space.w_nil
        space.globals.set(space, "$~", w_match)
        return w_match

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_RegexpObject(space, None, 0)

    @classdef.singleton_method("compile")
    def method_compile(self, space, args_w):
        w_obj = space.send(self, "allocate")
        return space.send(w_obj, "initialize", args_w)

    @classdef.method("initialize", flags="int")
    def method_initialize(self, space, w_source, flags=0):
        if isinstance(w_source, W_RegexpObject):
            self.set_source(space, w_source.source, w_source.flags)
        else:
            try:
                self.set_source(space, Coerce.str(space, w_source), flags)
            except regexp.RegexpError as e:
                raise space.error(space.w_RegexpError, str(e))
        return self

    @classdef.method("to_s")
    def method_to_s(self, space):
        flags = missing_flags = ""
        for c, f in regexp.FLAGS_MAP:
            if self.flags & f:
                flags += c
            else:
                missing_flags += c
        return space.newstr_fromstr("(?%s-%s:%s)" % (flags, missing_flags, self.source))

    @classdef.method("eql?")
    @classdef.method("==")
    def method_equal(self, space, w_other):
        if self is w_other:
            return space.w_true
        if not isinstance(w_other, W_RegexpObject):
            return space.w_false
        self._check_initialized(space)
        w_other._check_initialized(space)
        return space.newbool(self.source == w_other.source and (self.flags | regexp.NO_ENCODING) == (w_other.flags | regexp.NO_ENCODING))

    @classdef.method("source")
    def method_source(self, space):
        self._check_initialized(space)
        return space.newstr_fromstr(self.source)

    @classdef.method("=~")
    def method_match_operator(self, space, w_s):
        if w_s is space.w_nil:
            return space.w_nil
        s = Coerce.str(space, w_s)
        ctx = self.make_ctx(s)
        matched = rsre_core.search_context(ctx)
        self.get_match_result(space, ctx, s, matched)
        if matched:
            return space.newint(ctx.match_start)
        else:
            return space.w_nil

    @classdef.method("match")
    def method_match(self, space, w_s, w_offset=None):
        if w_s is space.w_nil:
            return space.w_nil
        s = Coerce.str(space, w_s)
        if w_offset is not None:
            offset = Coerce.int(space, w_offset)
        else:
            offset = 0
        ctx = self.make_ctx(s, offset)
        matched = rsre_core.search_context(ctx)
        return self.get_match_result(space, ctx, s, matched)

    @classdef.method("===", s="str")
    def method_eqeqeq(self, space, s):
        ctx = self.make_ctx(s)
        matched = rsre_core.search_context(ctx)
        self.get_match_result(space, ctx, s, matched)
        return space.newbool(matched)

    @classdef.method("casefold?")
    def method_casefoldp(self, space):
        return space.newbool(bool(self.flags & regexp.IGNORE_CASE))

    @classdef.singleton_method("quote", string="str")
    @classdef.singleton_method("escape", string="str")
    def method_escape(self, space, string):
        result = []
        for ch in string:
            result += RE_ESCAPE_TABLE[ord(ch)]
        return space.newstr_fromchars(result)

    @classdef.method("options")
    def method_options(self, space):
        return space.newint(self.flags)

    @classdef.method("fixed_encoding?")
    def method_fixed_encodingp(self, space):
        return space.newbool(bool(self.flags & regexp.FIXED_ENCODING))


class W_MatchDataObject(W_Object):
    classdef = ClassDef("MatchData", W_Object.classdef)

    def __init__(self, space, regexp, ctx, target):
        W_Object.__init__(self, space)
        self.regexp = regexp
        self.ctx = ctx
        self.target = target
        self._flatten_cache = None

    def size(self):
        offset = self.regexp.group_offsets[-1] if self.regexp.group_offsets else 0
        return self.regexp.groupcount + 1 - offset

    def flatten_marks(self):
        if self._flatten_cache is None:
            self._flatten_cache = self._build_flattened_marks(self.ctx, self.regexp.groupcount)
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
        n += self.regexp.group_offsets[n - 1]
        fmarks = self.flatten_marks()
        idx = 2 * (n - 1)
        assert idx >= 0
        return fmarks[idx], fmarks[idx + 1]

    @classdef.method("regexp")
    def method_regexp(self, space):
        return self.regexp

    @classdef.method("string")
    def method_string(self, space):
        res = space.newstr_fromstr(self.target)
        space.send(res, "freeze")
        return res

    @classdef.method("[]", n="int")
    def method_subscript(self, space, n):
        if n == 0:
            start, end = self.ctx.match_start, self.ctx.match_end
        elif 1 <= n < self.size():
            start, end = self.get_span(n)
        else:
            return space.w_nil
        if 0 <= start <= end:
            return space.newstr_fromstr(self.ctx._string[start:end])
        else:
            return space.w_nil

    @classdef.method("captures")
    def method_captures(self, space):
        res_w = []
        for i in xrange(1, self.size()):
            res_w.append(space.send(self, "[]", [space.newint(i)]))
        return space.newarray(res_w)

    @classdef.method("to_a")
    def method_to_a(self, space):
        res_w = []
        for i in xrange(self.size()):
            res_w.append(space.send(self, "[]", [space.newint(i)]))
        return space.newarray(res_w)

    @classdef.method("begin", n="int")
    def method_begin(self, space, n):
        if n == 0:
            start, _ = self.ctx.match_start, self.ctx.match_end
        elif 1 <= n < self.size():
            start, _ = self.get_span(n)
        else:
            raise space.error(space.w_IndexError, "index %d out of matches" % n)
        return space.newint(start)

    @classdef.method("end", n="int")
    def method_end(self, space, n):
        if n == 0:
            _, end = self.ctx.match_start, self.ctx.match_end
        elif 1 <= n < self.size():
            _, end = self.get_span(n)
        else:
            raise space.error(space.w_IndexError, "index %d out of matches" % n)
        return space.newint(end)

    @classdef.method("length")
    @classdef.method("size")
    def method_size(self, space):
        return space.newint(self.size())

    @classdef.method("pre_match")
    def method_pre_match(self, space):
        stop = self.ctx.match_start
        assert stop > 0
        return space.newstr_fromstr(self.ctx._string[:stop])

    @classdef.method("post_match")
    def method_post_match(self, space):
        return space.newstr_fromstr(self.ctx._string[self.ctx.match_end:])

    @classdef.method("values_at")
    def method_values_at(self, space, args_w):
        return space.send(
            space.send(self, "to_a"), "values_at", args_w
        )
