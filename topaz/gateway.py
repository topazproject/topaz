import functools

from rpython.rlib.unroll import unrolling_iterable

from topaz.coerce import Coerce


class WrapperGenerator(object):
    def __init__(self, name, func, argspec, self_cls):
        self.name = name
        self.func = func
        self.argspec = argspec
        self.self_cls = self_cls

    def generate_wrapper(self):
        if hasattr(self.func, "__wraps__"):
            wrapped_func = self.func.__wraps__
        else:
            wrapped_func = self.func

        code = wrapped_func.__code__
        if wrapped_func.__defaults__ is not None:
            defaults = wrapped_func.__defaults__
            default_start = code.co_argcount - len(defaults)
        else:
            defaults = []
            default_start = None
        argspec = self.argspec
        self_cls = self.self_cls
        func = self.func

        argnames = code.co_varnames[:code.co_argcount]
        argcount = 0
        for arg in argnames:
            argcount += arg.startswith("w_") or arg in argspec
        min_args = argcount
        for arg, default in zip(reversed(argnames), reversed(defaults)):
            min_args -= arg.startswith("w_") or arg in argspec
        unrolling_argnames = unrolling_iterable(enumerate(argnames))
        takes_args_w = "args_w" in argnames

        @functools.wraps(self.func)
        def wrapper(self, space, args_w, block):
            if (len(args_w) < min_args or
                    (not takes_args_w and len(args_w) > argcount)):
                raise space.error(
                    space.w_ArgumentError,
                    "wrong number of arguments (%d for %d)" % (
                        len(args_w), min_args))
            args = ()
            arg_count = 0
            args_w_seen = False
            for i, argname in unrolling_argnames:
                if argname == "self":
                    assert isinstance(self, self_cls)
                    args += (self,)
                elif argname == "args_w":
                    if args_w_seen:
                        raise SystemError("args_w cannot be repeated")
                    args += (args_w[arg_count:],)
                    args_w_seen = True
                elif argname == "block":
                    args += (block,)
                elif argname == "space":
                    args += (space,)
                elif argname.startswith("w_") or argname in argspec:
                    if args_w_seen:
                        raise SystemError(
                            "args_w must be the last argument accepted")
                    if len(args_w) > arg_count:
                        if argname.startswith("w_"):
                            args += (args_w[arg_count],)
                        elif argname in argspec:
                            args += (getattr(Coerce, argspec[argname])(
                                space, args_w[arg_count]),)
                    elif default_start is not None and i >= default_start:
                        args += (defaults[i - default_start],)
                    else:
                        raise SystemError("bad arg count")
                    arg_count += 1
                else:
                    raise SystemError("%r not implemented" % argname)
            w_res = func(*args)
            if w_res is None:
                w_res = space.w_nil
            return w_res
        return wrapper
