from pypy.rlib.rarithmetic import r_uint


pointerlen = 8 if r_uint.BITS > 32 else 4


def make_string_packer(padding=" ", nullterminated=False):
    def pack_string(packer, width):
        space = packer.space
        try:
            string = space.str_w(
                space.convert_type(packer.args_w[packer.args_index], space.w_string, "to_str")
            )
        except IndexError:
            raise space.error(space.w_ArgumentError, "too few arguments")
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

def pack_pointer(packer, repetitions):
    # Should return a C pointer string to a char* or struct*, but we
    # fake it to return just the right length, just as Rubinius does
    if repetitions > len(packer.args_w) - packer.args_index:
        raise packer.space.error(packer.space.w_ArgumentError, "too few arguments")
    for i in xrange(repetitions):
        for i in xrange(packer.args_index, repetitions + packer.args_index):
            packer.result.extend(["\0"] * pointerlen)
    packer.args_index += repetitions
