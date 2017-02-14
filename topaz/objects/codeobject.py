import copy

from topaz.module import ClassDef
from topaz.objects.objectobject import W_BaseObject


class W_CodeObject(W_BaseObject):
    _immutable_fields_ = [
        "code", "consts_w[*]", "max_stackdepth", "cellvars[*]", "freevars[*]",
        "arg_pos[*]", "defaults[*]", "block_arg_pos", "splat_arg_pos",
        "kwarg_names[*]", "kwrest_pos", "kw_defaults[*]", "default_arg_begin",
        "filepath", "lineno",
    ]

    classdef = ClassDef("Code", W_BaseObject.classdef)

    def __init__(self, name, filepath, line, code, max_stackdepth, consts, args,
                 splat_arg, kwargs, kwrest_arg, block_arg,
                 defaults, first_default_arg, kw_defaults,
                 cellvars, freevars, lineno_table):

        self.name = name
        self.filepath = filepath
        self.lineno = line
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts_w = consts
        self.defaults = defaults
        self.kwarg_names = kwargs
        self.kw_defaults = kw_defaults
        self.cellvars = cellvars
        self.freevars = freevars
        self.lineno_table = lineno_table

        n_args = len(args)
        arg_pos = [-1] * n_args
        for idx, arg in enumerate(args):
            arg_pos[idx] = cellvars.index(arg)
        self.arg_pos = arg_pos

        default_arg_begin = -1
        if first_default_arg:
            default_arg_begin = cellvars.index(first_default_arg)
        self.default_arg_begin = default_arg_begin

        splat_arg_pos = -1
        if splat_arg is not None:
            splat_arg_pos = cellvars.index(splat_arg)
        self.splat_arg_pos = splat_arg_pos

        kwrest_pos = -1
        if kwrest_arg is not None:
            kwrest_pos = cellvars.index(kwrest_arg)
        self.kwrest_pos = kwrest_pos

        block_arg_pos = -1
        if block_arg is not None:
            block_arg_pos = cellvars.index(block_arg)
        self.block_arg_pos = block_arg_pos

    def __deepcopy__(self, memo):
        obj = super(W_CodeObject, self).__deepcopy__(memo)
        obj.name = self.name
        obj.filepath = self.filepath
        obj.lineno = self.lineno
        obj.code = self.code
        obj.max_stackdepth = self.max_stackdepth
        obj.consts_w = copy.deepcopy(self.consts_w, memo)
        obj.defaults = copy.deepcopy(self.defaults, memo)
        obj.cellvars = self.cellvars
        obj.freevars = self.freevars
        obj.lineno_table = self.lineno_table
        obj.arg_pos = self.arg_pos
        obj.block_arg_pos = self.block_arg_pos
        obj.splat_arg_pos = self.splat_arg_pos
        obj.default_arg_begin = self.default_arg_begin
        obj.kw_defaults = self.kw_defaults
        obj.kwrest_pos = self.kwrest_pos
        obj.kwarg_names = self.kwarg_names
        return obj

    def arity(self, negative_defaults=False):
        args_count = len(self.arg_pos) - len(self.defaults)
        if self.splat_arg_pos != -1 or (negative_defaults and len(self.defaults) > 0):
            args_count = -(args_count + 1)
        return args_count

    @classdef.method("filepath")
    def method_filepath(self, space):
        return space.newstr_fromstr(self.filepath)
