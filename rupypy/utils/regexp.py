IGNORE_CASE = 1 << 0

SPECIAL_CHARS = "()|?*+{^$.[\\#"


class UnscopedFlagSet(Exception):
    def __init__(self, global_flags):
        Exception.__init__(self)
        self.global_flags = global_flags


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


class Info(object):
    def __init__(self, flags):
        self.flags = flags
        self.used_groups = {}
        self.named_lists_used = {}


class RegexpBase(object):
    pass


class Character(RegexpBase):
    def __init__(self, value, case_insensitive):
        RegexpBase.__init__(self)
        self.value = value
        self.case_insensitive = case_insensitive

    def fix_groups(self):
        pass

    def optimize(self, info):
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

    def compile(self):
        code = []
        for item in self.items:
            code.extend(item.compile())
        return code


def make_character(info, value, in_set=False):
    if in_set:
        return Character(value)
    return Character(value, case_insensitive=info.flags & IGNORE_CASE)


def make_sequence(items):
    if len(items) == 1:
        return items[0]
    return Sequence(items)


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

    code = parsed.compile()
    code.append(OPCODE_SUCCESS)

    if not parsed.has_simple_start():
        # Get the first set, if possible.
        try:
            fs_code = _compile_firstset(info, parsed.get_firstset())
            fs_code = _flatten_code(fs_code)
            code = fs_code + code
        except FirstSetError:
            pass

    index_group = dict((v, n) for n, v in info.group_index.items())
    return code, info.flags, info.group_index, index_group
