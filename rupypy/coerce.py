class Coerce(object):
    @staticmethod
    def symbol(space, w_obj):
        return space.symbol_w(w_obj)

    @staticmethod
    def int(space, w_obj):
        return space.int_w(w_obj)

    @staticmethod
    def float(space, w_obj):
        w_float_obj = space.send(w_obj, space.newsymbol("to_f"))
        return space.float_w(w_float_obj)

    @staticmethod
    def str(space, w_obj):
        return space.str_w(w_obj)

    @staticmethod
    def path(space, w_obj):
        if w_obj is space.w_nil:
            return None
        return space.str_w(w_obj)
