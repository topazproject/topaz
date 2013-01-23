from rpython.rlib.rstring import assert_str0


class Coerce(object):
    @staticmethod
    def bool(space, w_obj):
        return space.is_true(w_obj)

    @staticmethod
    def symbol(space, w_obj):
        if space.is_kind_of(w_obj, space.w_symbol):
            return space.symbol_w(w_obj)
        else:
            w_str = space.convert_type(w_obj, space.w_string, "to_str", raise_error=False)
            if w_str is space.w_nil:
                w_inspect_str = space.send(w_obj, space.newsymbol("inspect"))
                if not space.is_kind_of(w_inspect_str, space.w_string):
                    inspect_str = space.any_to_s(w_obj)
                else:
                    inspect_str = space.str_w(w_inspect_str)
                raise space.error(space.w_TypeError, "%s is not a symbol" % inspect_str)
            else:
                return space.str_w(w_str)

    @staticmethod
    def int(space, w_obj):
        if space.is_kind_of(w_obj, space.w_fixnum):
            return space.int_w(w_obj)
        else:
            return space.int_w(space.convert_type(w_obj, space.w_integer, "to_int"))

    @staticmethod
    def bigint(space, w_obj):
        return space.bigint_w(w_obj)

    @staticmethod
    def float(space, w_obj):
        if space.is_kind_of(w_obj, space.w_float):
            return space.float_w(w_obj)
        else:
            return space.float_w(space.send(w_obj, space.newsymbol("Float"), [w_obj]))

    @staticmethod
    def str(space, w_obj):
        if space.is_kind_of(w_obj, space.w_string) or space.is_kind_of(w_obj, space.w_symbol):
            return space.str_w(w_obj)
        else:
            return space.str_w(space.convert_type(w_obj, space.w_string, "to_str"))

    @staticmethod
    def path(space, w_obj):
        string = Coerce.str(space, w_obj)
        if "\x00" in string:
            raise space.error(space.w_ArgumentError, "string contains null byte")
        else:
            return assert_str0(string)
