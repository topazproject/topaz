def make_int_packer(size, signed, bigendian):
    def pack_int(space, packer, repetitions):
        if repetitions > len(packer.args_w) - packer.args_index:
            raise space.error(space.w_ArgumentError, "too few arguments")

        for i in xrange(packer.args_index, repetitions + packer.args_index):
            num = space.int_w(
                space.convert_type(packer.args_w[i], space.w_fixnum, "to_int")
            )
            if bigendian:
                for i in xrange(size - 1, -1, -1):
                    x = (num >> (8 * i)) & 0xff
                    packer.result.append(chr(x))
            else:
                for i in xrange(size - 1, -1, -1):
                    packer.result.append(chr(num & 0xff))
                    num >>= 8
        packer.args_index += repetitions
    return pack_int
