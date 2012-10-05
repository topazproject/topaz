from pypy.rlib.rstruct.ieee import float_pack
from pypy.rlib.rstruct.nativefmttable import native_is_bigendian

from rupypy.objects.intobject import W_FixnumObject
from rupypy.objects.floatobject import W_FloatObject


def make_float_packer(size=0, bigendian=native_is_bigendian):
    def pack_float(packer, repetitions):
        space = packer.space
        if repetitions > len(packer.args_w):
            raise space.error(space.w_ArgumentError, "too few arguments")
        for i in xrange(packer.args_index, repetitions + packer.args_index):
            w_item = packer.args_w[i]
            if not (isinstance(w_item, W_FloatObject) or isinstance(w_item, W_FixnumObject)):
                raise space.error(
                    space.w_TypeError,
                    "can't convert %s into Float" % space.getclass(w_item).name
                )
            doubleval = space.float_w(w_item)
            l = ["\0"] * size
            unsigned = float_pack(doubleval, size)
            for i in xrange(size):
                l[i] = chr((unsigned >> (i * 8)) & 0xff)
            if bigendian:
                l.reverse()
            packer.result.extend(l)
        packer.args_index += repetitions
    return pack_float
