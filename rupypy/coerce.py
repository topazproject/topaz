class Coerce(object):
    @staticmethod
    def bool(space, w_obj):
        return space.is_true(w_obj)

    @staticmethod
    def symbol(space, w_obj):
        return space.symbol_w(w_obj)

    @staticmethod
    def int(space, w_obj):
        return space.int_w(w_obj)

    @staticmethod
    def float(space, w_obj):
        from rupypy.objects.intobject import W_FixnumObject
        from rupypy.objects.numericobject import W_NumericObject
        if isinstance(w_obj, W_FixnumObject) or isinstance(w_obj, W_NumericObject):
            return space.float_w(w_obj)
        else:
            w_float_obj = space.send(w_obj, space.newsymbol("Float"), [w_obj])
            return space.float_w(w_float_obj)

    @staticmethod
    def str(space, w_obj):
        return space.str_w(w_obj)

    @staticmethod
    def path(space, w_obj):
        if w_obj is space.w_nil:
            return None
        return space.str_w(w_obj)
