from pypy.rlib.rsre.rsre_core import (OPCODE_LITERAL, OPCODE_SUCCESS,
    OPCODE_ASSERT, OPCODE_MARK, OPCODE_REPEAT, OPCODE_ANY, OPCODE_MAX_UNTIL,
    OPCODE_GROUPREF, OPCODE_AT)

IGNORE_CASE = 1 << 0
DOT_ALL = 1 << 1
MULTI_LINE = 1 << 2

SPECIAL_CHARS = "()|?*+{^$.[\\#"

AT_BEGINNING = 0
AT_BEGINNING_LINE = 1
AT_BEGINNING_STRING = 2
AT_BOUNDARY = 3
AT_NON_BOUNDARY = 4
AT_END = 5
AT_END_LINE = 6
AT_END_STRING = 7
AT_LOC_BOUNDARY = 8
AT_LOC_NON_BOUNDARY = 9
AT_UNI_BOUNDARY = 10
AT_UNI_NON_BOUNDARY = 11


class UnscopedFlagSet(Exception):
    def __init__(self, global_flags):
        Exception.__init__(self)
        self.global_flags = global_flags


class FirstSetError(Exception):
    pass


class RegexpError(Exception):
    pass


class Source(object):
    def __init__(self, s):
        self.pos = 0
        self.s = s

        self.ignore_space = False

    def at_end(self):
        s = self.s
        pos = self.pos

        if self.ignore_space:
            while True:
                if s[pos].isspace():
                    pos += 1
                elif s[pos] == "#":
                    pos = s.index("\n", pos)
                else:
                    break
        return pos >= len(s)

    def get(self):
        s = self.s
        pos = self.pos
        if self.ignore_space:
            while True:
                if s[pos].isspace():
                    pos += 1
                elif s[pos] == "#":
                    pos = s.index("\n", pos)
                else:
                    break
        try:
            ch = s[pos]
            self.pos = pos + 1
            return ch
        except IndexError:
            self.pos = pos
            return ""
        except ValueError:
            self.pos = len(s)
            return ""

    def match(self, substr):
        s = self.s
        pos = self.pos

        if self.ignore_space:
            for c in substr:
                while True:
                    if s[pos].isspace():
                        pos += 1
                    elif s[pos] == "#":
                        pos = s.index("\n", pos)
                    else:
                        break

                if s[pos] != c:
                    return False
                pos += 1
            self.pos = pos
            return True
        else:
            if not s.startswith(substr, pos):
                return False
            self.pos = pos + len(substr)
            return True

    def expect(self, substr):
        if not self.match(substr):
            raise RegexpBase("Missing %s" % substr)


class Info(object):
    OPEN = 0
    CLOSED = 1

    def __init__(self, flags):
        self.flags = flags

        self.group_count = 0
        self.used_groups = {}
        self.group_state = {}
        self.group_index = {}
        self.named_lists_used = {}
        self.defined_groups = {}

    def new_group(self, name=None):
        if name in self.group_index:
            if self.group_index[name] in self.used_groups:
                raise RegexpBase("duplicate group")
        else:
            while True:
                self.group_count += 1
                if name is None or self.group_count not in self.group_name:
                    break
            group = self.group_count
            if name is not None:
                self.group_index[name] = group
                self.group_name[group] = name
        self.used_groups[group] = None
        self.group_state[group] = self.OPEN
        return group

    def close_group(self, group):
        self.group_state[group] = self.CLOSED


class CompilerContext(object):
    def __init__(self):
        self.data = []

    def emit(self, opcode):
        self.data.append(opcode)

    def tell(self):
        return len(self.data)

    def patch(self, pos, value):
        self.data[pos] = value

    def build(self):
        return self.data


class Counts(object):
    def __init__(self, min_count, max_count=65535):
        self.min_count = min_count
        self.max_count = max_count


class RegexpBase(object):
    def __init__(self, positive=True, case_insensitive=False, zerowidth=False):
        self.positive = positive
        self.case_insensitive = case_insensitive
        self.zerowidth = zerowidth

    def with_flags(self, positive=None, case_insensitive=None, zerowidth=None):
        positive = positive if positive is not None else self.positive
        case_insensitive = case_insensitive if case_insensitive is not None else self.case_insensitive
        zerowidth = zerowidth if zerowidth is not None else self.zerowidth
        if (positive == self.positive and
            case_insensitive == self.case_insensitive and
            zerowidth == self.zerowidth):
            return self
        return self.rebuild(positive, case_insensitive, zerowidth)


class Character(RegexpBase):
    def __init__(self, value, case_insensitive=False, positive=True):
        RegexpBase.__init__(self, case_insensitive=case_insensitive, positive=positive)
        self.value = value

    def fix_groups(self):
        pass

    def optimize(self, info):
        return self

    def has_simple_start(self):
        return True

    def compile(self, ctx):
        ctx.emit(OPCODE_LITERAL_IGNORE if self.case_insensitive else OPCODE_LITERAL)
        ctx.emit(self.value)


class Any(RegexpBase):
    def is_empty(self):
        return False

    def fix_groups(self):
        pass

    def optimize(self, info):
        return self

    def has_simple_start(self):
        return True

    def compile(self, ctx):
        ctx.emit(OPCODE_ANY)


class ZeroWidthBase(RegexpBase):
    def fix_groups(self):
        pass

    def optimize(self, info, in_set=False):
        return self

    def has_simple_start(self):
        return False

    def get_firstset(self):
        return {None: None}


class StartOfString(ZeroWidthBase):
    def compile(self, ctx):
        ctx.emit(OPCODE_AT)
        ctx.emit(AT_BEGINNING_STRING)


class Range(RegexpBase):
    def __init__(self, lower, upper):
        RegexpBase.__init__(self)
        self.lower = lower
        self.upper = upper

    def optimize(self, info, in_set=False):
        return self


class Sequence(RegexpBase):
    def __init__(self, items):
        RegexpBase.__init__(self)
        self.items = items

    def fix_groups(self):
        for item in self.items:
            item.fix_groups()

    def optimize(self, info):
        items = []
        for item in self.items:
            item = item.optimize(info)
            if isinstance(item, Sequence):
                items.extend(item.items)
            else:
                items.append(item)
        return make_sequence(items)

    def has_simple_start(self):
        return self.items and self.items[0].has_simple_start()

    def compile(self, ctx):
        for item in self.items:
            item.compile(ctx)


class GreedyRepeat(RegexpBase):
    def __init__(self, subpattern, min_count, max_count):
        RegexpBase.__init__(self)
        self.subpattern = subpattern
        self.min_count = min_count
        self.max_count = max_count

    def fix_groups(self):
        self.subpattern.fix_groups()

    def optimize(self, info):
        subpattern = self.subpattern.optimize(info)
        return GreedyRepeat(subpattern, self.min_count, self.max_count)

    def is_empty(self):
        return self.subpattern.is_empty()

    def compile(self, ctx):
        ctx.emit(OPCODE_REPEAT)
        pos = ctx.tell()
        ctx.emit(0)
        ctx.emit(self.min_count)
        ctx.emit(self.max_count)
        self.subpattern.compile(ctx)
        ctx.patch(pos, ctx.tell() - pos)
        ctx.emit(OPCODE_MAX_UNTIL)


class LookAround(RegexpBase):
    def __init__(self, subpattern, behind, positive):
        RegexpBase.__init__(self, positive=positive)
        self.subpattern = subpattern
        self.behind = behind

    def fix_groups(self):
        self.subpattern.fix_groups()

    def optimize(self, info):
        return LookAround(self.subpattern.optimize(info), self.behind, self.positive)

    def compile(self, ctx):
        ctx.emit(OPCODE_ASSERT if self.positive else OPCODE_ASSERT_NOT)
        assert not self.behind
        pos = ctx.tell()
        ctx.emit(0)
        ctx.emit(0)
        self.subpattern.compile(ctx)
        ctx.emit(OPCODE_SUCCESS)
        ctx.patch(pos, ctx.tell() - pos)


class Group(RegexpBase):
    def __init__(self, info, group, subpattern):
        RegexpBase.__init__(self)
        self.info = info
        self.group = group
        self.subpattern = subpattern

    def fix_groups(self):
        self.info.defined_groups[self.group] = self
        self.subpattern.fix_groups()

    def optimize(self, info):
        return Group(self.info, self.group, self.subpattern.optimize(info))

    def has_simple_start(self):
        return self.subpattern.has_simple_start()

    def compile(self, ctx):
        ctx.emit(OPCODE_MARK)
        ctx.emit((self.group - 1) * 2)
        self.subpattern.compile(ctx)
        ctx.emit(OPCODE_MARK)
        ctx.emit((self.group - 1) * 2 + 1)


class RefGroup(RegexpBase):
    def __init__(self, info, group, case_insensitive=False):
        RegexpBase.__init__(self, case_insensitive=case_insensitive)
        self.info = info
        self.group = group

    def fix_groups(self):
        if not 1 <= self.group <= self.info.group_count:
            raise RegexpBase("unknown group")

    def optimize(self, info):
        return self

    def compile(self, ctx):
        assert not self.case_insensitive
        ctx.emit(OPCODE_GROUPREF)
        ctx.emit(self.group - 1)


class SetBase(RegexpBase):
    def __init__(self, info, items):
        RegexpBase.__init__(self)
        self.info = info
        self.items = items

    def is_empty(self):
        return False

    def fix_groups(self):
        pass


class SetUnion(SetBase):
    def optimize(self, info, in_set=False):
        items = []
        for item in self.items:
            item = item.optimize(info, in_set=True)
            if isinstance(item, SetUnion) and item.positive:
                items.extend(item.items)
            else:
                items.append(item)
        if len(items) == 1:
            return items[0].with_flags(
                positive=item.positive == self.positive,
                case_insensitive=self.case_insensitive,
                rzerowidth=self.zerowidth
            ).optimize(info, in_set=in_set)
        return SetUnion(self.info, items)

    def compile(self, ctx):
        raise NotImplementedError



def make_character(info, value, in_set=False):
    if in_set:
        return Character(value)
    return Character(value, case_insensitive=info.flags & IGNORE_CASE)


def make_sequence(items):
    if len(items) == 1:
        return items[0]
    return Sequence(items)


def make_atomic(info, subpattern):
    group = info.new_group()
    info.close_group(group)
    return Sequence([
        LookAround(Group(info, group, subpattern), behind=False, positive=True),
        RefGroup(info, group),
    ])


def _parse_pattern(source, info):
    previous_groups = info.used_groups.copy()
    branches = [_parse_sequence(source, info)]
    all_groups = info.used_groups
    while source.match("|"):
        info.used_groups = previous_groups.copy()
        branches.append(_parse_sequence(source, info))
        all_groups.update(info.used_groups)
    info.used_groups = all_groups

    if len(branches) == 1:
        return branches[0]
    return Branch(branches)


def _parse_sequence(source, info):
    sequence = []
    item = _parse_item(source, info)
    while item:
        sequence.append(item)
        item = _parse_item(source, info)

    return make_sequence(sequence)


def _parse_item(source, info):
    element = _parse_element(source, info)
    counts = _parse_quantifier(source, info)
    if counts is not None:
        min_count, max_count = counts.min_count, counts.max_count
        if source.match("?"):
            repeat_cls = LazyRepeat
        elif source.match("+"):
            repeat_cls = PossessiveRepeat
        else:
            repeat_cls = GreedyRepeat

        if element.is_empty() or min_count == max_count == 1:
            return element
        return repeat_cls(element, min_count, max_count)
    return element


def _parse_element(source, info):
    here = source.pos
    ch = source.get()
    if ch in SPECIAL_CHARS:
        if ch in ")|":
            source.pos = here
            return None
        elif ch == "\\":
            return _parse_escape(source, info, in_set=False)
        elif ch == "(":
            element = _parse_paren(source, info)
            if element is not None:
                return element
        elif ch == ".":
            if info.flags & DOT_ALL:
                return AnyAll()
            else:
                return Any()
        elif ch == "[":
            return _parse_set(source, info)
        elif ch == "^":
            if info.flags & MULTI_LINE:
                return StartOfLine()
            else:
                return StartOfString()
        elif ch == "$":
            if info.flags & MULTI_LINE:
                return EndOfLine()
            else:
                return EndOfString()
        elif ch == "{":
            here2 = source.pos
            counts = _parse_quantifier(source, info)
            if counts is not None:
                raise RegexpError("nothing to repeat")
            source.pos = here2
            return make_character(info, ord(ch))
        elif ch in "?*+":
            raise RegexpError("nothing to repeat")
        else:
            return make_character(info, ord(ch))
    else:
        return make_character(info, ord(ch))


def _parse_quantifier(source, info):
    while True:
        here = source.pos
        if source.match("?"):
            return Counts(0, 1)
        elif source.match("*"):
            return Counts(0)
        elif source.match("+"):
            return Counts(1)
        elif source.match("{"):
            try:
                return _parse_limited_quantifier(source)
            except ParseError:
                pass
        elif source.match("(?#"):
            parse_comment(source)
            continue
        break
    source.pos = here
    return None


def _parse_paren(source, info):
    if source.match("?"):
        if source.match("<"):
            if source.match("="):
                return _parse_lookaround(source, info, behind=True, positive=True)
            elif source.match("!"):
                return _parse_lookaround(source, info, behind=True, positive=False)
            name = _parse_name(source)
            group = info.new_group(name)
            source.expect(">")
            saved_flags = info.flags
            saved_ignore = source.ignore_space
            try:
                subpattern = _parse_pattern(source, info)
            finally:
                source.ignore_space = saved_ignore
                info.flags = saved_flags
            source.expect(")")
            info.close_group(group)
            return Group(info, group, subpattern)
        elif source.match("="):
            return _parse_lookaround(source, info, behind=False, positive=True)
        elif source.match("!"):
            return _parse_lookaround(source, info, behind=False, positive=False)
        elif source.match("#"):
            _parse_comment(source)
            return
        elif source.match("("):
            return _parse_conditional(source, info)
        elif source.match(">"):
            return _parse_atomic(source, info)
        elif source.match("|"):
            return _parse_common(source, info)
        else:
            here = source.pos
            ch = source.get()
            if ch == "R" or "0" <= ch <= "9":
                return _parse_call_group(source, info, ch)
            elif ch == "&":
                return _parse_call_named_group(source, info)
            else:
                source.pos = here
                return _parse_flags_subpattern(source, info)
    group = info.new_group()
    saved_flags = info.flags
    saved_ignore = source.ignore_space
    try:
        subpattern = _parse_pattern(source, info)
    finally:
        source.ignore_space = saved_ignore
        info.flags = saved_flags
    source.expect(")")
    info.close_group(group)
    return Group(info, group, subpattern)


def _parse_atomic(source, info):
    saved_flags = info.flags
    saved_ignore = source.ignore_space
    try:
        subpattern = _parse_pattern(source, info)
    finally:
        source.ignore_space = saved_ignore
        info.flags = saved_flags
    source.expect(")")
    return make_atomic(info, subpattern)


def _parse_set(source, info):
    saved_ignore = source.ignore_space
    source.ignore_space = False
    negate = source.match("^")
    try:
        item = _parse_set_intersect(source, info)
        source.expect("]")
    finally:
        source.ignore_space = saved_ignore

    if negate:
        items = item.with_flags(positive=not item.positive)
    return item.with_flags(case_insensitive=info.flags & IGNORE_CASE)


def _parse_set_intersect(source, info):
    items = [_parse_set_implicit_union(source, info)]
    while source.match("&&"):
        items.append(_parse_set_implicit_union(source, info))

    if len(items) == 1:
        return items[0]
    return SetIntersection(info, items)


def _parse_set_implicit_union(source, info):
    items = [_parse_set_member(source, info)]
    while True:
        here = source.pos
        if source.match("]"):
            source.pos = here
            break
        if source.match("&&"):
            source.pos = here
            break
        items.append(_parse_set_member(source, info))
    if len(items) == 1:
        return items[0]
    return SetUnion(info, items)


def _parse_set_member(source, info):
    start = _parse_set_item(source, info)
    if (not isinstance(start, Character) or not start.positive or
        not source.match("-")):
        return start

    here = source.pos
    if source.match("]"):
        source.pos = here
        return SetUnion(info, [start, Character(ord("-"))])
    end = _parse_set_item(source, info)
    if not isinstance(end, Character) or not end.positive:
        return SetUnion(info, [start, Character(ord("-")), end])
    if start.value > end.value:
        raise RegexpError("bad character range")
    if start.value == end.value:
        return start
    return Range(start.value, end.value)


def _parse_set_item(source, info):
    if source.match("\\"):
        return _parse_escape(source, info, in_set=True)

    here = source.pos
    if source.match("[:"):
        try:
            return _parse_posix_class(source, info)
        except ParseError:
            source.pos = here
    if source.match("["):
        negate = source.match("^")
        item = _parse_set_intersect(source, info)
        source.expect("]")
        if negate:
            item = item.with_flags(positive=not item.positive)
        return item
    ch = source.get()
    if not ch:
        raise RegexpError("bad set")
    return Character(ord(ch))


def _compile_firstset(info, fs):
    if not fs or None in fs:
        return []
    members = {}
    for i in fs:
        if i.case_insensitive:
            if isinstance(i, Character):
                if _is_cased(info, i.value):
                    return []
            elif isinstance(i, SetBase):
                return []
        members[i.with_flags(case_insensitive=False)] = None
    fs = SetUnion(info, list(members), zerowidth=True)
    fs = fs.optimize(info, in_set=True)
    ctx = CompilerContext()
    fs.compile(ctx)
    return ctx.build()


def compile(pattern, flags=0):
    global_flags = flags
    while True:
        source = Source(pattern)
        info = Info(flags)
        try:
            parsed = _parse_pattern(source, info)
        except UnscopedFlagSet as e:
            global_flags = e.flags | flags
        else:
            break

    if not source.at_end():
        raise RegexpError("trailing characters in pattern")

    parsed.fix_groups()
    parsed = parsed.optimize(info)

    # regex.py:510
    assert not info.named_lists_used

    ctx = CompilerContext()
    parsed.compile(ctx)
    ctx.emit(OPCODE_SUCCESS)
    code = ctx.build()

    if not parsed.has_simple_start():
        # Get the first set, if possible.
        try:
            fs_code = _compile_firstset(info, parsed.get_firstset())
            code = fs_code + code
        except FirstSetError:
            pass

    index_group = dict([(v, n) for n, v in info.group_index.iteritems()])
    return code, info.flags, info.group_count, info.group_index, index_group
