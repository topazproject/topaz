import os

from pypy.rlib.rsre import rsre_core
from pypy.rlib.rstring import StringBuilder

from rupypy.objects.fileobject import FNM_NOESCAPE, FNM_DOTMATCH
from rupypy.utils import regexp


def regexp_match(re, string, _flags=0):
    pos = 0
    endpos = len(string)
    code, flags, _, _, _, _ = regexp.compile(re, _flags)
    return rsre_core.StrMatchContext(code, string, pos, endpos, flags)


class Glob(object):
    def __init__(self, matches=None):
        self._matches = matches or []

    def matches(self):
        return self._matches

    def append_match(self, match):
        self._matches.append(match)

    def path_split(self, string):
        ret = []
        ctx = regexp_match("/+", string)

        last_end = 0
        while rsre_core.search_context(ctx):
            cur_start, cur_end = ctx.match_start, ctx.match_end
            assert cur_start >= 0
            assert cur_end >= cur_start
            ret.append(string[last_end:cur_start])
            ret.append(string[cur_start:cur_end])
            last_end = cur_end
            ctx.reset(last_end)

        if last_end > 0:
            ret.append(string[last_end:])
        else:
            ret.append(string)

        if ret:
            while len(ret[-1]) == 0:
                ret.pop()

        return ret

    def single_compile(self, glob, flags=0):
        parts = self.path_split(glob)

        if glob[-1] == "/":
            last = DirectoriesOnly(None, flags)
        else:
            file = parts.pop()
            ctx = regexp_match("^[a-zA-Z0-9._]+$", file)
            if rsre_core.search_context(ctx):
                last = ConstantEntry(None, flags, file)
            else:
                last = EntryMatch(None, flags, file)

        while parts:
            last.separator = parts.pop()
            dir = parts.pop()
            if dir == "**":
                if parts:
                    last = RecursiveDirectories(last, flags)
                else:
                    last = StartRecursiveDirectories(last, flags)
            else:
                pattern = "^[^\*\?\]]+"
                ctx = regexp_match(pattern, dir)
                if rsre_core.search_context(ctx):
                    partidx = len(parts) - 2
                    assert partidx >= 0
                    ctx = regexp_match(pattern, parts[partidx])

                    while rsre_core.search_context(ctx):
                        next_sep = parts.pop()
                        next_sect = parts.pop()
                        dir = next_sect + next_sep + dir

                        partidx = len(parts) - 2
                        assert partidx >= 0
                        ctx = regexp_match(pattern, parts[partidx])
                    last = ConstantDirectory(last, flags, dir)
                elif len(dir) > 0:
                    last = DirectoryMatch(last, flags, dir)

        if glob[0] == "/":
            last = RootDirectory(last, flags)
        return last

    def run(self, node):
        node.call(self, None)

    def glob(self, pattern, flags):
        if "{" in pattern:
            patterns = self.compile(pattern, flags)
            for node in patterns:
                self.run(node)
        else:
            node = self.single_compile(pattern, flags)
            if node:
                self.run(node)

    def compile(self, pattern, flags=0, patterns=None):
        if patterns is None:
            patterns = []

        escape = flags & FNM_NOESCAPE == 0
        rbrace = -1
        lbrace = -1

        i = pattern.find("{")
        if i > -1:
            nest = 0
            while i < len(pattern):
                char = pattern[i]
                if char == "{":
                    lbrace = i
                    nest += 1
                elif char == "}":
                    nest -= 1

                if nest == 0:
                    rbrace = i
                    break

                if char == "\\" and escape:
                    escape = True
                    i += 1
                i += 1

        if lbrace >= 0 and rbrace >= 0:
            pos = lbrace
            front = pattern[:lbrace]
            back = pattern[rbrace + 1:len(pattern)]

            while pos < rbrace:
                nest = 0
                pos += 1
                last = pos

                while pos < rbrace and not (pattern[pos] == "?" and nest == 0):
                    if pattern[pos] == "{":
                        nest += 1
                    elif pattern[pos] == "}":
                        nest -= 1

                    if pattern[pos] == "\\" and escape:
                        pos += 1
                        if pos == rbrace:
                            break
                    pos += 1

                brace_pattern = front + pattern[last:pos] + back
                self.compile(brace_pattern, flags, patterns)
        else:
            node = self.single_compile(pattern, flags)
            if node:
                patterns.append(node)
        return patterns


class Node(object):
    def __init__(self, nxt, flags):
        self.flags = flags
        self.next = nxt
        self.separator = "/"

    def path_join(self, parent, ent):
        if not parent:
            return ent
        if parent == "/":
            return "/" + ent
        else:
            return parent + self.separator + ent


class ConstantDirectory(Node):
    def __init__(self, nxt, flags, dir):
        Node.__init__(self, nxt, flags)
        self.dir = dir

    def call(self, glob, path):
        full = self.path_join(path, self.dir)
        self.next.call(glob, full)


class ConstantEntry(Node):
    def __init__(self, nxt, flags, name):
        Node.__init__(self, nxt, flags)
        self.name = name

    def call(self, glob, parent):
        path = self.path_join(parent, self.name)
        if os.path.exists(path):
            glob.append_match(path)


class RootDirectory(Node):
    def call(self, glob, path):
        self.next.call(glob, "/")


class RecursiveDirectories(Node):
    def call(self, glob, start):
        if not (start and os.path.exists(start)):
            return
        self.call_with_stack(glob, start, [start])

    def allow_dots(self):
        return self.flags & FNM_DOTMATCH != 0

    def call_with_stack(self, glob, start, stack):
        old_sep = self.next.separator
        self.next.separator = self.separator
        self.next.call(glob, start)
        self.next.separator = old_sep

        while stack:
            path = stack.pop()
            try:
                entries = os.listdir(path)
            except OSError:
                continue
            for ent in entries:
                full = self.path_join(path, ent)
                if os.path.isdir(full) and (self.allow_dots() or ent[0] != "."):
                    stack.append(full)
                    self.next.call(glob, full)


class StartRecursiveDirectories(RecursiveDirectories):
    def call(self, glob, start):
        stack = []
        for ent in os.listdir("."):
            if os.path.isdir(ent) and (self.allow_dots() or ent[0] != "."):
                stack.append(ent)
                self.next.call(glob, ent)
        self.call_with_stack(glob, None, stack)


class Match(Node):
    def __init__(self, nxt, flags, glob_pattern):
        Node.__init__(self, nxt, flags)
        self.regexp = self.translate(glob_pattern, flags)

    # Copied from stdlib, but rpython and uses StringBuilder instead of string concat
    def translate(self, pattern, flags):
        pattern = os.path.normcase(pattern)
        i = 0
        n = len(pattern)
        res = StringBuilder(n)
        res.append("^")
        while i < n:
            c = pattern[i]
            i += 1
            if c == "*":
                res.append(".*")
                # skip second `*' in directory wildcards
                if i < n and pattern[i] == "*":
                    i += 1
            elif c == "?":
                res.append(".")
            elif c == "[":
                j = i
                if j < n and pattern[j] == "!":
                    j += 1
                if j < n and pattern[j] == "]":
                    j += 1
                while j < n and pattern[j] != "]":
                    j += 1
                if j >= n:
                    res.append("\\[")
                else:
                    res.append("[")
                    if pattern[i] == "!":
                        res.append("^")
                        i += 1
                    elif pattern[i] == "^":
                        res.append("\\^")
                        i += 1
                    for ch in pattern[i:j]:
                        if ch == "\\":
                            res.append("\\\\")
                        else:
                            res.append(ch)
                    res.append("]")
                    i = j + 1
            else:
                if not c.isalnum():
                    res.append("\\")
                res.append(c)
        res.append("$")
        return res.build()

    def ismatch(self, string):
        string = os.path.normcase(string)
        ctx = regexp_match(self.regexp, string)
        return rsre_core.search_context(ctx)


class DirectoryMatch(Match):
    def call(self, glob, path):
        if path and not os.path.exists(path):
            return

        for ent in os.listdir(path if path else "."):
            if self.ismatch(ent):
                full = self.path_join(path, ent)
                if os.path.isdir(full):
                    self.next.call(glob, full)


class EntryMatch(Match):
    def call(self, glob, path):
        if path and not os.path.exists(path + "/."):
            return

        try:
            entries = os.listdir(path if path else ".")
        except OSError:
            return

        for ent in entries:
            if self.ismatch(ent):
                glob.append_match(self.path_join(path, ent))


class DirectoriesOnly(Node):
    def call(self, glob, path):
        if path and os.path.exists(path + "/."):
            glob.append_match(path + "/")
