from rpython.rtyper.lltypesystem import rffi, lltype


def select_conversion_method(size, signed):
    if signed:
        if size <= rffi.sizeof(lltype.Signed):
            return "intmask_w"
        else:
            return "longlongmask_w"
    else:
        if size < rffi.sizeof(lltype.Signed):
            return "intmask_w"
        elif size == rffi.sizeof(lltype.Signed):
            return "uintmask_w"
        else:
            return "ulonglongmask_w"


def make_int_packer(size, signed, bigendian):
    conversion_method = select_conversion_method(size, signed)

    def pack_int(space, packer, repetitions):
        if repetitions > len(packer.args_w) - packer.args_index:
            raise space.error(space.w_ArgumentError, "too few arguments")

        for i in xrange(packer.args_index, repetitions + packer.args_index):
            w_num = space.convert_type(packer.args_w[i], space.w_integer, "to_int")
            num = getattr(w_num, conversion_method)(space)
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
