from topaz.coerce import Coerce


class WrapperGenerator(object):
    def __init__(self, name, func, argspec, self_cls):
        self.name = name
        self.func = func
        self.argspec = argspec
        self.self_cls = self_cls

    def generate_wrapper(self):
        code = self.func.__code__

        lines = []
        lines.append("def %s(self, space, args_w, block):" % self.func.__name__)
        lines.append("    if ((len(args_w) < (argcount - len(defaults)) or")
        lines.append("        (not takes_args_w and len(args_w) > argcount))):")
        lines.append("        raise space.error(space.w_ArgumentError,")
        lines.append("            'wrong number of arguments (%d for %d)' % (len(args_w), argcount - len(defaults))")
        lines.append("        )")
        lines.append("    args = ()")
        if self.func.__defaults__ is not None:
            default_start = code.co_argcount - len(self.func.__defaults__)
        else:
            default_start = None

        self.arg_count = 0

        for i, argname in enumerate(code.co_varnames[:code.co_argcount]):
            if argname in self.argspec or argname.startswith("w_"):
                if argname.startswith("w_"):
                    coerce_code = "args_w[{:d}]".format(self.arg_count)
                else:
                    spec = self.argspec[argname]
                    coerce_code = "Coerce.{}(space, args_w[{:d}])".format(spec, self.arg_count)
                lines.append("    if len(args_w) > {}:".format(self.arg_count))
                lines.append("        args += ({},)".format(coerce_code))
                lines.append("    else:")
                if default_start is not None and i >= default_start:
                    lines.append("        args += (defaults[{:d}],)".format(i - default_start))
                else:
                    lines.append("        raise SystemError('bad arg count')")
                self.arg_count += 1
            elif argname == "self":
                lines.append("    assert isinstance(self, self_cls)")
                lines.append("    args += (self,)")
            elif argname == "args_w":
                lines.append("    args += (args_w,)")
            elif argname == "block":
                lines.append("    args += (block,)")
            elif argname == "space":
                lines.append("    args += (space,)")
            else:
                raise NotImplementedError(argname, self.func.__name__)

        lines.append("    w_res = func(*args)")
        lines.append("    if w_res is None:")
        lines.append("        w_res = space.w_nil")
        lines.append("    return w_res")

        source = "\n".join(lines)
        namespace = {
            "func": self.func,
            "self_cls": self.self_cls,
            "Coerce": Coerce,
            "defaults": self.func.__defaults__ or [],
            "argcount": self.arg_count,
            "takes_args_w": "args_w" in code.co_varnames[:code.co_argcount],
        }
        exec source in namespace
        return namespace[self.func.__name__]
