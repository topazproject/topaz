from rpython.rtyper.lltypesystem import rffi


def make_string_packer(padding=" ", nullterminated=False):
    def pack_string(space, packer, width):
        try:
            w_s = packer.args_w[packer.args_index]
        except IndexError:
            raise space.error(space.w_ArgumentError, "too few arguments")
        string = space.str_w(space.convert_type(w_s, space.w_string, "to_str"))
        if nullterminated:
            packer.result += string
            packer.result.append("\0")
        else:
            assert width >= 0
            string = string[:width]
            packer.result += string
            packer.result.extend([padding] * (width - len(string)))
        packer.args_index += 1
    return pack_string


def pack_pointer(space, packer, repetitions):
    # Should return a C pointer string to a char* or struct*, but we
    # fake it to return just the right length, just as Rubinius does
    if repetitions > len(packer.args_w) - packer.args_index:
        raise space.error(space.w_ArgumentError, "too few arguments")
    for i in xrange(repetitions):
        for i in xrange(packer.args_index, repetitions + packer.args_index):
            packer.result.extend(["\0"] * rffi.sizeof(rffi.INTPTR_T))
    packer.args_index += repetitions
