from pypy.rlib.rsre.rsre_char import SRE_INFO_PREFIX, SRE_INFO_LITERAL
from pypy.rlib.rsre.rsre_core import (OPCODE_SUCCESS, OPCODE_INFO,
    OPCODE_LITERAL, OPCODE_ANY, OPCODE_MARK)
from pypy.rlib.runicode import MAXUNICODE

from rupypy.utils import re_parse
from rupypy.utils.re_consts import (FLAG_IGNORECASE, FLAG_DOTALL, LITERAL,
    SUBPATTERN, BRANCH, IN, NOT_LITERAL, ANY, REPEAT, MIN_REPEAT, MAX_REPEAT)


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
                op, av = av[1][0]
                if op == LITERAL:
                    charset.append((op, av))
                elif op == BRANCH:
                    c = []
                    for p in av[1]:
                        if not p:
                            break
                        op, av = p[0]
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
                    op, av = p[0]
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
        mask += INFO_CHARSET
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
            raise NotImplementedError(op, "sre_compile:L42")
        elif op == IN:
            raise NotImplementedError(op, "sre_compile:L48")
        elif op == ANY:
            if flags & FLAG_DOTALL:
                code.append(OPCODE_ANY_ALL)
            else:
                code.append(OPCODE_ANY)
        elif op in [REPEAT, MIN_REPEAT, MAX_REPEAT]:
            raise NotImplementedError(op, "sre_compile:L64")
        elif op == SUBPATTERN:
            if av[0]:
                code.append(OPCODE_MARK)
                code.append((av[0] - 1) * 2)
            _compile(code, av[1].data, flags)
            if av[0]:
                code.append(OPCODE_MARK)
                code.append((av[0] - 1) * 2 + 1)
        else:
            raise NotImplementedError(op, "sre_compile:L48")


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
