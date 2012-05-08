from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_CodeObject(W_BaseObject):
    _immutable_fields_ = [
        "code", "consts_w[*]", "max_stackdepth", "locals[*]", "cellvars[*]",
        "freevars[*]", "arg_locs[*]", "arg_pos[*]", "defaults[*]"
    ]

    classdef = ClassDef("Code", W_BaseObject.classdef)

    UNKNOWN = 0
    LOCAL = 1
    CELL = 2

    def __init__(self, name, filepath, code, max_stackdepth, consts, args,
                 block_arg, defaults, locals, cellvars, freevars):

        self.name = name
        self.filepath = filepath
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts_w = consts
        self.defaults = defaults
        self.locals = locals
        self.cellvars = cellvars
        self.freevars = freevars

        n_args = len(args)
        arg_locs = [self.UNKNOWN] * n_args
        arg_pos = [-1] * n_args
        for idx, arg in enumerate(args):
            if arg in locals:
                arg_locs[idx] = self.LOCAL
                arg_pos[idx] = locals.index(arg)
            elif arg in cellvars:
                arg_locs[idx] = self.CELL
                arg_pos[idx] = cellvars.index(arg)
        self.arg_locs = arg_locs
        self.arg_pos = arg_pos

        block_arg_pos = -1
        block_arg_loc = self.UNKNOWN
        if block_arg is not None:
            if block_arg in locals:
                block_arg_loc = self.LOCAL
                block_arg_pos = locals.index(block_arg)
            elif arg in cellvars:
                block_arg_loc = self.CELL
                block_arg_pos = cellvars.index(arg)
        self.block_arg_loc = block_arg_loc
        self.block_arg_pos = block_arg_pos

    @classdef.method("filepath")
    def method_filepath(self, space):
        return space.newstr_fromstr(self.filepath)
