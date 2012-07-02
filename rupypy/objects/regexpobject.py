import re

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_RegexpObject(W_Object):
    classdef = ClassDef("Regexp", W_Object.classdef)

    def __init__(self, space, regexp):
        W_Object.__init__(self, space)
        self.regexp = regexp

    @classdef.method("source")
    def method_source(self, space):
        return space.newstr_fromstr(self.regexp)

    @classdef.method("=~", string="str")
    def method_match(self, space, string):
        if space.globals.get("$=") is not None and space.is_true(space.globals.get("$=")):
            regexp = re.compile(self.regexp, re.I)
        else:
            regexp = re.compile(self.regexp)
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
