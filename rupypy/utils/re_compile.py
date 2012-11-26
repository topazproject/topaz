from pypy.rlib.rsre.rsre_char import (SRE_INFO_PREFIX, SRE_INFO_LITERAL,
    SRE_INFO_CHARSET)
from pypy.rlib.rsre.rsre_core import (OPCODE_SUCCESS, OPCODE_INFO,
    OPCODE_LITERAL, OPCODE_ANY, OPCODE_MARK, OPCODE_AT, OPCODE_IN,
    OPCODE_RANGE, OPCODE_FAILURE, OPCODE_BRANCH, OPCODE_NOT_LITERAL,
    OPCODE_REPEAT_ONE, OPCODE_CHARSET, OPCODE_NEGATE, OPCODE_REPEAT,
    OPCODE_MAX_UNTIL, OPCODE_ASSERT_NOT)
from pypy.rlib.runicode import MAXUNICODE

from rupypy.utils import re_parse
from rupypy.utils.re_consts import (FLAG_IGNORECASE, FLAG_DOTALL, MAXREPEAT,
    LITERAL, SUBPATTERN, BRANCH, IN, NOT_LITERAL, ANY, REPEAT, MIN_REPEAT,
    MAX_REPEAT, SUCCESS, FAILURE, ASSERT, ASSERT_NOT, CALL, AT, NEGATE, RANGE,
    CHARSET)


def _compile_info(code, pattern, flags):
    lo, hi = pattern.getwidth()
    if lo == 0:
        return
    prefix = []
    prefix_skip = 0
    charset = []
    if not (flags & FLAG_IGNORECASE):
        for op, av in pattern.data:
            if op == LITERAL:
                if len(prefix) == prefix_skip:
                    prefix_skip += 1
                prefix.append(av)
            elif op == SUBPATTERN and len(av[1].data) == 1:
                op, av = av[1].data[0]
                if op == LITERAL:
                    prefix.append(av)
                else:
                    break
            else:
                break
        if not prefix and pattern.data:
            op, av = pattern.data[0]
            if op == SUBPATTERN:
                op, av = av[1].data[0]
                if op == LITERAL:
                    charset.append((op, av))
                elif op == BRANCH:
                    c = []
                    for p in av[1]:
                        if not p:
                            break
                        op, av = p.data[0]
                        if op == LITERAL:
                            c.append((op, av))
                        else:
                            break
                    else:
                        charset = c
            elif op == BRANCH:
                c = []
                for p in av[1]:
                    if not p:
                        break
                    op, av = p.data[0]
                    if op == LITERAL:
                        c.append((op, av))
                    else:
                        break
                else:
                    charset = c
            elif op == IN:
                charset = av
    code.append(OPCODE_INFO)
    skip = len(code)
    code.append(0)
    mask = 0
    if prefix:
        mask = SRE_INFO_PREFIX
        if len(prefix) == prefix_skip == len(pattern.data):
            mask += SRE_INFO_LITERAL
    elif charset:
        mask += SRE_INFO_CHARSET
    code.append(mask)
    if lo < MAXUNICODE:
        code.append(lo)
    else:
        code.append(MAXUNICODE)
        prefix = prefix[:MAXUNICODE]
    if hi < MAXUNICODE:
        code.append(hi)
    else:
        code.append(0)

    if prefix:
        code.append(len(prefix))
        code.append(prefix_skip)
        code.extend(prefix)
        table = [-1] + [0] * len(prefix)
        for i in xrange(len(prefix)):
            table[i + 1] = table[i] + 1
            while table[i + 1] > 0 and prefix[i] != prefix[table[i + 1] - 1]:
                table[i + 1] = table[table[i + 1] - 1] + 1
        code.extend(table[1:])
    elif charset:
        _compile_charset(code, charset, flags)
    code[skip] = len(code) - skip


def _compile(code, pattern, flags):
    for op, av in pattern:
        if op == LITERAL:
            # TODO: sre_compile:L43
            assert not flags & FLAG_IGNORECASE
            code.append(OPCODE_LITERAL)
            code.append(av)
        elif op == NOT_LITERAL:
            # TODO: sre_compile:L43
            assert not flags & FLAG_IGNORECASE
            code.append(OPCODE_NOT_LITERAL)
            code.append(av)
        elif op == IN:
            assert not flags & FLAG_IGNORECASE
            code.append(OPCODE_IN)
            skip = len(code)
            code.append(0)
            _compile_charset(code, av, flags)
            code[skip] = len(code) - skip
        elif op == ANY:
            if flags & FLAG_DOTALL:
                code.append(OPCODE_ANY_ALL)
            else:
                code.append(OPCODE_ANY)
        elif op in [REPEAT, MIN_REPEAT, MAX_REPEAT]:
            if _simple(av) and op != REPEAT:
                if op == MAX_REPEAT:
                    code.append(OPCODE_REPEAT_ONE)
                else:
                    code.append(OPCODE_MIN_REPEAT_ONE)
                skip = len(code)
                code.append(0)
                code.append(av[0])
                code.append(av[1])
                _compile(code, av[2].data, flags)
                code.append(OPCODE_SUCCESS)
                code[skip] = len(code) - skip
            else:
                code.append(OPCODE_REPEAT)
                skip = len(code)
                code.append(0)
                code.append(av[0])
                code.append(av[1])
                _compile(code, av[2].data, flags)
                code[skip] = len(code) - skip
                if op == MAX_REPEAT:
                    code.append(OPCODE_MAX_UNTIL)
                else:
                    code.append(OPCODE_MIN_UNTIL)
        elif op == SUBPATTERN:
            if av[0]:
                code.append(OPCODE_MARK)
                code.append((av[0] - 1) * 2)
            _compile(code, av[1].data, flags)
            if av[0]:
                code.append(OPCODE_MARK)
                code.append((av[0] - 1) * 2 + 1)
        elif op in [SUCCESS, FAILURE]:
            raise NotImplementedError(op, "sre_compile:L106")
        elif op == ASSERT:
            raise NotImplementedError(op, "sre_compile:L108")
        elif op == ASSERT_NOT:
            code.append(OPCODE_ASSERT_NOT)
            skip = len(code)
            code.append(0)
            if av[0] >= 0:
                code.append(0)
            else:
                lo, hi = av[1].getwidth()
                assert lo == hi
                code.append(lo)
            _compile(code, av[1].data, flags)
            code.append(OPCODE_SUCCESS)
            code[skip] = len(code) - skip
        elif op == CALL:
            raise NotImplementedError(op, "sre_compile:L121")
        elif op == AT:
            code.append(OPCODE_AT)
            assert not flags
            code.append(av)
        elif op == BRANCH:
            code.append(OPCODE_BRANCH)
            tails = []
            for av in av[1]:
                skip = len(code)
                code.append(0)
                _compile(code, av.data, flags)
                tails.append(len(code))
                code.append(0)
                code[skip] = len(code) - skip
            code.append(0)
            for tail in tails:
                code[tail] = len(code) - tail
        else:
            raise NotImplementedError(op, "sre_compile:L150")


def _compile_charset(code, charset, flags):
    for op, av in _optimize_charset(charset):
        if op == NEGATE:
            code.append(OPCODE_NEGATE)
            pass
        elif op == LITERAL:
            code.append(OPCODE_LITERAL)
            code.append(av)
        elif op == RANGE:
            code.append(OPCODE_RANGE)
            code.append(av[0])
            code.append(av[1])
        elif op == CHARSET:
            code.append(OPCODE_CHARSET)
            code.extend(av)
        elif op == BIGCHARSET:
            code.append(OPCODE_BIGCHARSET)
            code.extend(av)
        elif op == CATEGORY:
            raise NotImplementedError(op, av, "sre_compile:L196")
        else:
            raise SystemError("Unsupport opcode for set: %d" % op)
    code.append(OPCODE_FAILURE)


def _optimize_charset(charset):
    out = []
    charmap = [False] * 256
    for op, av in charset:
        if op == NEGATE:
            out.append((NEGATE, av))
        elif op == LITERAL:
            charmap[av] = True
        elif op == RANGE:
            for i in range(av[0], av[1] + 1):
                charmap[i] = True
        elif op == CATEGORY:
            return charset
    i = p = n = 0
    runs = []
    for c in charmap:
        if c:
            if p == 0:
                p = i
            n += 1
        elif n:
            runs.append((p, n))
            n = 0
        i += 1
    if n:
        runs.append((p, n))
    if len(runs) <= 2:
        for p, n in runs:
            if n == 1:
                out.append((LITERAL, p))
            else:
                out.append((RANGE, (p, p + n - 1)))
        if len(out) < len(charset):
            return out
    else:
        data = _mk_bitmap(charmap)
        out.append((CHARSET, data))
        return out
    return charset


def _mk_bitmap(bits):
    data = []
    m = 1
    v = 0
    for c in bits:
        if c:
            v += m
        m += m
        if m > MAXUNICODE:
            data.append(v)
            m = 1
            v = 0
    return data


def _simple(av):
    lo, hi = av[2].getwidth()
    assert lo != 0 or hi != MAXREPEAT
    return lo == hi == 1 and av[2].data[0][0] != SUBPATTERN


def _code(p, flags):
    flags = p.pattern.flags | flags
    code = []
    _compile_info(code, p, flags)
    _compile(code, p.data, flags)
    code.append(OPCODE_SUCCESS)
    return code


def compile(source, flags):
    p = re_parse.parse(source, flags)
    code = _code(p, flags)

    groupindex = p.pattern.groupdict
    indexgroup = [None] * p.pattern.num_groups
    for k, i in groupindex.iteritems():
        indexgroup[i] = k
    return code, flags, groupindex, indexgroup
