import fnmatch
import os

from pypy.rlib.rsre import rsre_core

from rupypy.utils import regexp


FNM_NOESCAPE = 0x1
FNM_DOTMATCH = 0x4

def regexp_match(re, string, _flags=0):
    pos = 0
    endpos = len(string)
    code, flags, _, _, _, _ = regexp.compile(re, _flags)
    return rsre_core.StrMatchContext(code, string, pos, endpos, flags)


class Glob(object):
    def path_split(self, string):
        start = 0
        ret = []
        last_match = None
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
            last.set_separator(parts.pop())
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

    def run(self, node, matches=None):
        if matches is None:
            matches = []
        env = Environment(matches)
        node.call(env, None)
        return env.matches

    def glob(self, pattern, flags, matches=None):
        if matches is None:
            matches = []

        if "{" in pattern:
            patterns = self.compile(pattern, flags)
            for node in patterns:
                self.run(node, matches)
        else:
            node = self.single_compile(pattern, flags)
            if node:
                return self.run(node, matches)
            else:
                return matches

    def compile(self, pattern, flags=0, patterns=None):
        if patterns is None:
            patterns = []

        escape = flags & FNM_NOESCAPE == 0
        rbrace = -1
        lbrace = -1
        escapes = False

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
                    escapes = True
                    i += 1
                i += 1

        if lbrace > -1 and rbrace > -1:
            pos = lbrace
            assert lbrace >= 0 # XXX: why does the translator need this?
            front = pattern[0:lbrace]
            backstart = rbrace + 1
            assert backstart >= 0
            back = pattern[backstart:len(pattern)]

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
        self.separator = None

    def set_separator(self, value):
        self.separator = value

    def get_separator(self):
        return self.separator or "/"

    def path_join(self, parent, ent):
        if not parent:
            return ent
        if parent == "/":
            return "/" + ent
        else:
            return parent + self.get_separator() + ent


class ConstantDirectory(Node):
    def __init__(self, nxt, flags, dir):
        Node.__init__(self, nxt, flags)
        self.dir = dir

    def call(self, env, path):
        full = self.path_join(path, self.dir)
        self.next.call(env, full)


class ConstantEntry(Node):
    def call(self, env, parent):
        path = self.path_join(parent, self.name)
        if os.path.exists(path):
            env.matches.append(path)


class RootDirectory(Node):
    def call(self, env, path):
        self.next.call(env, "/")


class RecursiveDirectories(Node):
    def call(self, env, start):
        if not (start and os.path.exists(start)):
            return
        self.call_with_stack(env, start, [start])

    def allow_dots(self):
        return self.flags & FNM_DOTMATCH != 0

    def call_with_stack(self, env, start, stack):
        old_sep = self.next.get_separator()
        self.next.set_separator(self.separator)
        self.next.call(env, start)
        self.next.set_separator(old_sep)

        while stack:
            path = stack.pop()
            try:
                for ent in os.listdir(path):
                    full = self.path_join(path, ent)
                    if os.path.isdir(full) and (self.allow_dots() or ent[0] != "."):
                        stack.append(full)
                        self.next.call(env, full)
            except OSError:
                # ignore listing errors
                next


class StartRecursiveDirectories(RecursiveDirectories):
    def call(self, env, start):
        if start:
            raise "invalid usage"
        stack = []
        for ent in os.listdir("."):
            if os.path.isdir(ent) and (self.allow_dots() or ent[0] != "."):
                stack.append(ent)
                self.next.call(env, ent)
        self.call_with_stack(env, start, stack)


class Match(Node):
    def __init__(self, nxt, flags, glob):
        Node.__init__(self, nxt, flags)
        self.glob = glob

    def ismatch(self, string):
        return fnmatch.fnmatch(string, self.glob)


class DirectoryMatch(Match):
    def __init__(self, nxt, flags, glob):
        Match.__init__(self, nxt, flags, glob)
        self.glob.replace("**", "*")

    def call(self, env, path):
        if path and not os.path.exists(path):
            return

        for ent in os.listdir(path if path else "."):
            if self.ismatch(ent):
                full = self.path_join(path, ent)
                if os.path.isdir(full):
                    self.next.call(env, full)


class EntryMatch(Match):
    def call(self, env, path):
        if path and not os.path.exists(path + "/."):
            return

        try:
            entries = os.listdir(path if path else ".")
        except OSError:
            return

        for ent in entries:
            if self.ismatch(ent):
                env.matches.append(self.path_join(path, ent))


class DirectoriesOnly(Node):
    def call(self, env, path):
        if path and os.path.exists(path + "/."):
            env.matches.append(path + "/")


class Environment(object):
    def __init__(self, matches=None):
        if matches is None:
            self.matches = []
        else:
            self.matches = matches
