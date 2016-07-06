import os

from collections import OrderedDict

from rpython.rlib.rsre import rsre_core
from rpython.rlib.rstring import StringBuilder

from topaz.objects.fileobject import FNM_NOESCAPE, FNM_DOTMATCH
from topaz.utils import regexp
from topaz.utils.ll_file import isdir


def regexp_match(cache, re, string):
    pos = 0
    endpos = len(string)
    code, flags, _, _, _, _ = regexp.compile(cache, re)
    return rsre_core.StrMatchContext(code, string, pos, endpos, flags)


def path_split(string):
    if not string:
        return [""]
    parts = []
    for part in string.split("/"):
        parts.append("/")
        if part:
            parts.append(part)
    return parts[1:]


def combine_segments(old_segments, suffix, new_segments=[""]):
    segments = []
    for old_seg in old_segments:
        for new_seg in new_segments:
            segments.append(old_seg + suffix + new_seg)
    return segments


class Glob(object):
    def __init__(self, cache, matches=None):
        self.cache = cache
        self._matches = OrderedDict()
        for match in (matches or []):
            self.append_match(match)

    def matches(self):
        return self._matches.keys()

    def append_match(self, match):
        self._matches[match] = None

    def is_constant(self, part, flags):
        special_chars = "?*["
        if not (flags & FNM_NOESCAPE):
            special_chars += "\\"
        for ch in part:
            if ch in special_chars:
                return False
        return True

    def single_compile(self, glob, flags=0):
        parts = path_split(glob)

        if parts[-1] == "/":
            last = DirectoriesOnly(None, flags)
        else:
            file = parts.pop()
            if self.is_constant(file, flags):
                last = ConstantEntry(None, flags, file)
            else:
                last = EntryMatch(None, flags, file)

        while parts:
            sep_parts = []
            while parts and parts[-1] == "/":
                sep_parts.append(parts.pop())
            last.separator = "".join(sep_parts)
            if not parts:
                last = RootDirectory(last, flags)
            else:
                dir = parts.pop()
                if dir == "**":
                    if parts:
                        last = RecursiveDirectories(last, flags)
                    else:
                        last = StartRecursiveDirectories(last, flags)
                elif self.is_constant(dir, flags):
                    last = ConstantDirectory(last, flags, dir)
                else:
                    last = DirectoryMatch(last, flags, dir)

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

    def process_braces(self, pattern, flags, i=0):
        should_escape = flags & FNM_NOESCAPE == 0
        patterns = []

        escaped = False
        pattern_start = i
        segments = [""]
        while i < len(pattern):
            ch = pattern[i]
            if ch == "\\" and should_escape and not escaped:
                escaped = True
            elif ch == ",":
                if escaped:
                    escaped = False
                else:
                    suffix = pattern[pattern_start:i]
                    patterns.extend(combine_segments(segments, suffix))
                    segments = [""]
                    pattern_start = i + 1
            elif ch == "}":
                if escaped:
                    escaped = False
                else:
                    suffix = pattern[pattern_start:i]
                    patterns.extend(combine_segments(segments, suffix))
                    return i, patterns
            elif ch == "{":
                if escaped:
                    escaped = False
                else:
                    suffix = pattern[pattern_start:i]
                    i, new_segs = self.process_braces(pattern, flags, i + 1)
                    segments = combine_segments(segments, suffix, new_segs)
                    pattern_start = i + 1
            else:
                escaped = False
            i += 1

        suffix = pattern[pattern_start:]
        patterns.extend(combine_segments(segments, suffix))
        return i, patterns

    def compile(self, pattern, flags=0):
        i, patterns = self.process_braces(pattern, flags)
        return [self.single_compile(p) for p in patterns]


class Node(object):
    def __init__(self, nxt, flags):
        self.flags = flags
        self.next = nxt
        self.separator = "/"

    def allow_dots(self):
        return self.flags & FNM_DOTMATCH != 0

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
                if isdir(full) and (self.allow_dots() or ent[0] != "."):
                    stack.append(full)
                    self.next.call(glob, full)


class StartRecursiveDirectories(RecursiveDirectories):
    def call(self, glob, start):
        stack = []
        for ent in os.listdir("."):
            if isdir(ent) and (self.allow_dots() or ent[0] != "."):
                stack.append(ent)
                self.next.call(glob, ent)
        self.call_with_stack(glob, None, stack)


class Match(Node):
    def __init__(self, nxt, flags, glob_pattern):
        Node.__init__(self, nxt, flags)
        self.match_dotfiles = self.allow_dots() or glob_pattern[0] == "."
        self.regexp = self.translate(glob_pattern, flags)

    def translate(self, pattern, flags):
        pattern = os.path.normcase(pattern)
        should_escape = flags & FNM_NOESCAPE == 0
        escaped = False
        i = 0
        n = len(pattern)
        res = StringBuilder(n)
        res.append("^")
        while i < n:
            c = pattern[i]
            i += 1
            if c == "\\":
                if should_escape and not escaped:
                    escaped = True
                else:
                    res.append("\\\\")
                    escaped = False
            elif c == "*":
                if escaped:
                    escaped = False
                    res.append("\\*")
                else:
                    res.append(".*")
                    # skip second `*' in directory wildcards
                    if i < n and pattern[i] == "*":
                        i += 1
            elif c == "?":
                if escaped:
                    escaped = False
                    res.append("\\?")
                else:
                    res.append(".")
            elif c == "[":
                if escaped:
                    escaped = False
                    res.append("\\[")
                else:
                    j = i
                    if j < n and pattern[j] == "^":
                        j += 1
                    if j < n and pattern[j] == "]":
                        j += 1
                    while j < n and pattern[j] != "]":
                        j += 1
                    if j >= n:
                        res.append("\\[")
                    else:
                        res.append("[")
                        if pattern[i] == "^":
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
                escaped = False
                if not c.isalnum():
                    res.append("\\")
                res.append(c)
        res.append("$")
        return res.build()

    def ismatch(self, cache, string):
        string = os.path.normcase(string)
        if string.startswith(".") and not self.match_dotfiles:
            return False
        ctx = regexp_match(cache, self.regexp, string)
        return rsre_core.search_context(ctx)


class DirectoryMatch(Match):
    def call(self, glob, path):
        if path and not os.path.exists(path):
            return

        for ent in [".", ".."] + os.listdir(path if path else "."):
            if self.ismatch(glob.cache, ent):
                full = self.path_join(path, ent)
                if isdir(full):
                    self.next.call(glob, full)


class EntryMatch(Match):
    def call(self, glob, path):
        if path and not os.path.exists(path + "/."):
            return

        try:
            entries = [".", ".."] + os.listdir(path if path else ".")
        except OSError:
            return

        for ent in entries:
            if self.ismatch(glob.cache, ent):
                glob.append_match(self.path_join(path, ent))


class DirectoriesOnly(Node):
    def call(self, glob, path):
        if path and os.path.exists(path + "/."):
            if path == "/":
                glob.append_match("/")
            else:
                glob.append_match(path + "/")
