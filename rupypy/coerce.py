class Coerce(object):
    @staticmethod
    def symbol(ec, w_obj):
        return ec.space.symbol_w(w_obj)

    @staticmethod
    def int(ec, w_obj):
        return ec.space.int_w(w_obj)

    @staticmethod
    def float(ec, w_obj):
        w_float_obj = ec.space.send(ec, w_obj, ec.space.newsymbol("to_f"))
        return ec.space.float_w(w_float_obj)

    @staticmethod
    def str(ec, w_obj):
        return ec.space.str_w(w_obj)

    @staticmethod
    def path(ec, w_obj):
        if w_obj is ec.space.w_nil:
            return None
        return ec.space.str_w(w_obj)
