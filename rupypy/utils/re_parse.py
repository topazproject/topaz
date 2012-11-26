import string
import sys

from pypy.rlib.rsre.rsre_core import (AT_BEGINNING, AT_BEGINNING_STRING,
    AT_END, AT_BOUNDARY, AT_NON_BOUNDARY)

from rupypy.utils.re_consts import (LITERAL, BRANCH, CALL, SUBPATTERN,
    REPEAT, MIN_REPEAT, MAX_REPEAT, ANY, RANGE, IN, NOT_LITERAL, CATEGORY, AT,
    SUCCESS, NEGATE)


PATTERN_ENDERS = "|)"
SPECIAL_CHARS = ".\\[{()*+?^$|"
REPEAT_CHARS = "*+?{"

ESCAPES = {
    r"\a": (LITERAL, ord("\a")),
    r"\b": (LITERAL, ord("\b")),
    r"\f": (LITERAL, ord("\f")),
    r"\n": (LITERAL, ord("\n")),
    r"\r": (LITERAL, ord("\r")),
    r"\t": (LITERAL, ord("\t")),
    r"\v": (LITERAL, ord("\v")),
    r"\\": (LITERAL, ord("\\"))
}

CATEGORIES = {
    r"\A": (AT, AT_BEGINNING_STRING),
    r"\b": (AT, AT_BOUNDARY),
    r"\B": (AT, AT_NON_BOUNDARY),
    # r"\d": (IN, [(CATEGORY, CATEGORY_DIGIT)]),
    # r"\D": (IN, [(CATEGORY, CATEGORY_NOT_DIGIT)]),
    # r"\s": (IN, [(CATEGORY, CATEGORY_SPACE)]),
    # r"\S": (IN, [(CATEGORY, CATEGORY_NOT_SPACE)]),
    # r"\w": (IN, [(CATEGORY, CATEGORY_WORD)]),
    # r"\W": (IN, [(CATEGORY, CATEGORY_NOT_WORD)]),
    # r"\Z": (AT, AT_END_STRING),
}

class RegexpError(Exception):
    pass


class Tokenizer(object):
    def __init__(self, source):
        self.source = source
        self.idx = 0
        self._advance()

    def _advance(self):
        if self.idx >= len(self.source):
            self.next = None
            return None
        char = self.source[self.idx]
        if char == "\\":
            try:
                c = self.source[self.idx + 1]
            except IndexError:
                raise RegexpError("bogus escape (end of line)")
            char += c
        self.idx += len(char)
        self.next = char

    def get(self):
        c = self.next
        self._advance()
        return c

    def match(self, c, skip=True):
        if c == self.next:
            if skip:
                self._advance()
            return True
        return False


class Pattern(object):
    def __init__(self, source, flags):
        self.source = source
        self.flags = flags
        self.open = []
        self.num_groups = 1
        self.groupdict = {}

    def opengroup(self, name=None):
        gid = self.num_groups
        self.num_groups += 1
        if name is not None:
            assert name not in self.groupdict
            self.groupdict[name] = gid
        self.open.append(gid)
        return gid

    def closegroup(self, gid):
        self.open.remove(gid)


class SubPattern(object):
    def __init__(self, pattern, data=None):
        self.pattern = pattern
        if data is None:
            data = []
        self.data = data

    def append(self, code):
        self.data.append(code)

    def getwidth(self):
        lo = hi = 0
        for op, av in self.data:
            if op == BRANCH:
                i = sys.maxint
                j = 0
                for av in av[1]:
                    l, h = av.getwidth()
                    i = min(i, l)
                    j = max(j, h)
                lo += i
                hi += j
            elif op == CALL:
                i, j = av.getwidth()
                lo += i
                hi += j
            elif op == SUBPATTERN:
                i, j = av[1].getwidth()
                lo += i
                hi += j
            elif op in [MIN_REPEAT, MAX_REPEAT]:
                i, j = av[2].getwidth()
                lo += (i * av[0])
                hi += (j * av[1])
            elif op in [ANY, RANGE, IN, LITERAL, NOT_LITERAL, CATEGORY]:
                lo += 1
                hi += 1
            elif op == SUCCESS:
                break
        return min(lo, sys.maxint), min(hi, sys.maxint)


def _parse_sub(source, state, nested=True):
    items = []
    while True:
        items.append(_parse(source, state))
        if source.match("|"):
            continue
        if not nested:
            break
        if not source.next or source.match(")", skip=False):
            break
        else:
            raise RegexpError("pattern not properly closed")

    if len(items) == 1:
        return items[0]

    subpattern = SubPattern(state)
    while True:
        prefix = None
        for item in items:
            if not item:
                break
            if prefix is None:
                prefix = item.data[0]
            elif item.data[0] != prefix:
                break
        else:
            for item in items:
                del item.data[0]
            subpattern.append(prefix)
            continue
        break

    for item in items:
        if len(item.data) != 1 or item.data[0][0] != LITERAL:
            break
    else:
        charset = []
        for item in items:
            charset.append(item.data[0])
        subpattern.append((IN, charset))
        return subpattern

    subpattern.append((BRANCH, (None, items)))
    return subpattern


def _parse(source, state):
    subpattern = SubPattern(state)
    while True:
        if source.next and source.next in PATTERN_ENDERS:
            break
        c = source.get()
        if c is None:
            break

        if c and c[0] not in SPECIAL_CHARS:
            subpattern.append((LITERAL, ord(c)))
        elif c == "[":
            charset = []
            if source.match("^"):
                charset.append((NEGATE, None))
            start = charset[:]
            while True:
                c = source.get()
                if c == "]" and charset != start:
                    break
                elif c and c[0] == "\\":
                    code1 = _class_escape(source, c)
                elif c:
                    code1 = LITERAL, ord(c)
                else:
                    raise RegexpError("unexpected end of regular expression")
                if source.match("-"):
                    c = source.get()
                    if c == "]":
                        if code1[0] == IN:
                            code1 = code1[1][0]
                        charset.append(code1)
                        charset.append((LITERAL, ord("-")))
                    elif c:
                        if c[0] == "\\":
                            code2 = _class_escape(source, c)
                        else:
                            code2 = LITERAL, ord(c)
                        if code1[0] != LITERAL or code2[0] != LITERAL:
                            raise RegexpError("bad character range")
                        lo = code1[1]
                        hi = code2[1]
                        if hi < lo:
                            raise RegexpError("bad character range")
                        charset.append((RANGE, (lo, hi)))
                    else:
                        raise RegexpError("unexpected end of regular expression")
                else:
                    if code1[0] == IN:
                        code1 = code1[1][0]
                    charset.append(code1)

            if len(charset) == 1 and charset[0][0] == LITERAL:
                subpattern.append(charset[0])
            elif len(charset) == 2 and charset[0][0] == NEGATE and charset[1][0] == LITERAL:
                subpattern.append((NOT_LITERAL, charset[1][1]))
            else:
                subpattern.append((IN, charset))
        elif c and c[0] in REPEAT_CHARS:
            if c == "?":
                min, max = 0, 1
            elif c == "*":
                min, max = 0, MAX_REPEAT
            elif c == "+":
                min, max = 1, MAX_REPEAT
            elif c == "{":
                if source.next == "}":
                    subpattern.append((LITERAL, ord(c)))
                here = source.tell()
                min, max = 0, MAX_REPEAT
                lo = hi = ""
                while source.next in DIGITS:
                    lo += source.get()
                if source.match(","):
                    while source.next in DIGITS:
                        hi += source.get()
                else:
                    hi = lo
                if not source.match("}"):
                    subpattern.append((LITERAL, ord(c)))
                    source.seek(here)
                    continue
                if lo:
                    min = int(lo)
                if hi:
                    max = int(hi)
                if max < min:
                    raise RegexpError("bad repeat interval")
            else:
                raise RegexpError("not supported")
            if subpattern:
                item = subpattern.data[-1:]
            else:
                item = None
            if not item or (len(item) == 1 and item[0][0] == AT):
                raise RegexpError("nothing to repeat")
            if item[0][0] in [REPEAT, MIN_REPEAT, MAX_REPEAT]:
                raise RegexpError("multiple repeat")
            if item is not None:
                item = SubPattern(subpattern.pattern, item)
            if source.match("?"):
                subpattern.data[-1] = (MIN_REPEAT, (min, max, item))
            else:
                subpattern.data[-1] = (MAX_REPEAT, (min, max, item))
        elif c == ".":
            subpattern.append((ANY, None))
        elif c == "(":
            group = 1
            name = None
            condgroup = None
            if source.match("?"):
                raise NotImplementedError("sre_parse:L528")
            if group:
                if group == 2:
                    group = None
                else:
                    group = state.opengroup(name)
                if condgroup:
                    p = _parse_sub_cond(source, state, condgroup)
                else:
                    p = _parse_sub(source, state)
                if not source.match(")"):
                    raise RegexpError("unbalanced parenthesis")
                if group is not None:
                    state.closegroup(group)
                subpattern.append((SUBPATTERN, (group, p)))
            else:
                char = source.get()
                if char is None:
                    raise RegexpError("unexpected end of pattern")
                if char != ")":
                    raise RegexpError("unknown extension")
        elif c == "^":
            subpattern.append((AT, AT_BEGINNING))
        elif c == "$":
            subpattern.append((AT, AT_END))
        elif c and c[0] == "\\":
            subpattern.append(_escape(source, c, state))
        else:
            raise RegexpError("parser error")
    return subpattern


def _class_escape(source, escape):
    if escape in ESCAPES:
        return ESCAPES[escape]
    if escape in CATEGORIES:
        return CATEGORIES[escape]
    c = escape[1:2]
    if c == "x":
        raise NotImplementedError("sre_parse:L236")
    elif c in string.octdigits:
        raise NotImplementedError("sre_parse:L244")
    elif c.isdigit():
        raise NotImplementedError("sre_parse:L250")
    if len(escape) == 2:
        return LITERAL, ord(c)
    raise RegexpError("bogus escape: %r" % escape)


def _escape(source, escape, state):
    if escape in CATEGORIES:
        return CATEGORIES[escape]
    if escape in ESCAPES:
        return ESCAPES[escape]
    c = escape[1:2]
    if c == "x":
        raise NotImplementedError("sre_parse:L268")
    elif c == "0":
        raise NotImplementedError("sre_parse:L275")
    elif c.isdigit():
        raise NotImplementedError("sre_parse:L281")
    if len(escape) == 2:
        return LITERAL, ord(c)
    raise RegexpError("bogus escape: %r" % escape)


def parse(source, flags):
    t = Tokenizer(source)
    pattern = Pattern(source, flags)

    p = _parse_sub(t, pattern, False)
    tail = t.get()
    if tail == ")":
        raise RegexpError("unbalanced parenthesis")
    elif tail:
        raise RegexpError("bogus characters at end of regular expression")
    return p
