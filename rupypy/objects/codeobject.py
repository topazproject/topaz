import copy

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_CodeObject(W_BaseObject):
    _immutable_fields_ = [
        "code", "consts_w[*]", "max_stackdepth", "locals[*]", "cellvars[*]",
        "freevars[*]", "arg_locs[*]", "arg_pos[*]", "defaults[*]",
        "block_arg_loc", "block_arg_pos", "splat_arg_loc", "splat_arg_pos",
    ]

    classdef = ClassDef("Code", W_BaseObject.classdef)

    UNKNOWN = 0
    LOCAL = 1
    CELL = 2

    def __init__(self, name, filepath, code, max_stackdepth, consts, args,
                 splat_arg, block_arg, defaults, locals, cellvars, freevars,
                 lineno_table):

        self.name = name
        self.filepath = filepath
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts_w = consts
        self.defaults = defaults
        self.locals = locals
        self.cellvars = cellvars
        self.freevars = freevars
        self.lineno_table = lineno_table

        n_args = len(args)
        arg_locs = [self.UNKNOWN] * n_args
        arg_pos = [-1] * n_args
        for idx, arg in enumerate(args):
            arg_locs[idx], arg_pos[idx] = self._get_arg_pos_loc(arg, locals, cellvars)
        self.arg_locs = arg_locs
        self.arg_pos = arg_pos

        block_arg_loc = self.UNKNOWN
        block_arg_pos = -1
        if block_arg is not None:
            block_arg_loc, block_arg_pos = self._get_arg_pos_loc(block_arg, locals, cellvars)
        self.block_arg_loc = block_arg_loc
        self.block_arg_pos = block_arg_pos

        splat_arg_loc = self.UNKNOWN
        splat_arg_pos = -1
        if splat_arg is not None:
            splat_arg_loc, splat_arg_pos = self._get_arg_pos_loc(splat_arg, locals, cellvars)
        self.splat_arg_loc = splat_arg_loc
        self.splat_arg_pos = splat_arg_pos

    def __deepcopy__(self, memo):
        obj = super(W_CodeObject, self).__deepcopy__(memo)
        obj.name = self.name
        obj.filepath = self.filepath
        obj.code = self.code
        obj.max_stackdepth = self.max_stackdepth
        obj.consts_w = copy.deepcopy(self.consts_w, memo)
        obj.defaults = copy.deepcopy(self.defaults, memo)
        obj.locals = self.locals
        obj.cellvars = self.cellvars
        obj.freevars = self.freevars
        obj.lineno_table = self.lineno_table
        obj.arg_locs = self.arg_locs
        obj.arg_pos = self.arg_pos
        obj.block_arg_loc = self.block_arg_loc
        obj.block_arg_pos = self.block_arg_pos
        obj.splat_arg_loc = self.splat_arg_loc
        obj.splat_arg_pos = self.splat_arg_pos
        return obj

    def _get_arg_pos_loc(self, arg, locals, cellvars):
        if arg in locals:
            loc = self.LOCAL
            pos = locals.index(arg)
        elif arg in cellvars:
            loc = self.CELL
            pos = cellvars.index(arg)
        else:
            raise SystemError
        return loc, pos

    @classdef.method("filepath")
    def method_filepath(self, space):
        return space.newstr_fromstr(self.filepath)
