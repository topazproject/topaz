from rpython.rlib import rfloat
from rpython.rlib.rstruct.ieee import float_pack

from topaz.objects.floatobject import W_FloatObject
from topaz.objects.intobject import W_FixnumObject


def make_float_packer(size, bigendian):
    def pack_float(space, packer, repetitions):
        if repetitions > len(packer.args_w) - packer.args_index:
            raise space.error(space.w_ArgumentError, "too few arguments")
        for i in xrange(packer.args_index, repetitions + packer.args_index):
            w_item = packer.args_w[i]
            if not (isinstance(w_item, W_FloatObject) or isinstance(w_item, W_FixnumObject)):
                raise space.error(space.w_TypeError,
                    "can't convert %s into Float" % space.obj_to_s(space.getclass(w_item))
                )
            doubleval = space.float_w(w_item)
            l = ["\0"] * size
            try:
                unsigned = float_pack(doubleval, size)
            except OverflowError:
                unsigned = float_pack(rfloat.copysign(rfloat.INFINITY, doubleval), size)
            for i in xrange(size):
                l[i] = chr((unsigned >> (i * 8)) & 0xff)
            if bigendian:
                l.reverse()
            packer.result.extend(l)
        packer.args_index += repetitions
    return pack_float
