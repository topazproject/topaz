from rupypy.utils.re import re_rffi as re
from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object

class W_RegexpObject(W_Object):
    classdef = ClassDef("Regexp", W_Object.classdef)

    def __init__(self, space, regexp, options=0):
        W_Object.__init__(self, space)
        # TODO: we still need to pass in the encoding flag
        self.regexp = regexp
        self.options = options
        
    @classdef.singleton_method("compile", regexp="str")
    @classdef.singleton_method("new", regexp="str")
    def method_new(self, space, regexp):
        return W_RegexpObject(space, regexp)

    @classdef.method("source")
    def method_source(self, space):
        return space.newstr_fromstr(self.regexp)

    @classdef.method("=~", string="str")
    def method_match(self, space, string):
        if space.globals.get("$=") is not None and space.is_true(space.globals.get("$=")):
            # recompile the regexp
            regexp = re.compile(self.regexp, re.I)
        else:
            regexp = re.compile(self.regexp, self.options)
            
        match = regexp.search(string)
        if match is None:
            for glob in ["$%d" % i for i in xrange(1, 10)] + ["$&", "$+", "$`", "$'", "$~"]:
                space.globals.set(glob, space.w_nil)
            return space.w_nil
        else:
            for i in xrange(1, min(regexp.groups + 1, 10)):
                space.globals.set("$%d" % i, space.newstr_fromstr(match.group(i)))
            space.globals.set("$&", space.newstr_fromstr(string[match.start():match.end()]))
            space.globals.set("$+", space.newstr_fromstr(match.group(regexp.groups)))
            space.globals.set("$`", space.newstr_fromstr(string[0:match.start()]))
            space.globals.set("$'", space.newstr_fromstr(string[match.end():len(string)]))
        return space.newint(match.start())

    @classdef.method("==")
    @classdef.method("eql?")
    def method_equal(self, space, w_other):
        assert isinstance(w_other, W_RegexpObject)
        s = re.compile(self.regexp, self.options)
        o = re.compile(w_other.regexp, w_other.options)
        return space.newbool(
                s.pattern == o.pattern
                and (s.flags & re.I) == (o.flags & re.I)
                and s.encoding() == o.encoding())

    @classdef.method("encoding")
    def method_encoding(self, space):
        # TODO: return a Encoding-Object instead of a string
        return space.newstr_fromstr(re.compile(self.regexp, self.options).encoding())

    @classdef.method("casefold?")
    def method_casefold(self, space):
        return space.newbool(self.options & re.I)