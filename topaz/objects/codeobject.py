import copy

from topaz.module import ClassDef
from topaz.objects.objectobject import W_BaseObject


class W_CodeObject(W_BaseObject):
    _immutable_fields_ = [
        "code", "consts_w[*]", "max_stackdepth", "cellvars[*]", "freevars[*]",
        "arg_pos[*]", "defaults[*]", "block_arg_pos", "splat_arg_pos",
    ]

    classdef = ClassDef("Code", W_BaseObject.classdef, filepath=__file__)

    def __init__(self, name, filepath, code, max_stackdepth, consts, args,
                 splat_arg, block_arg, defaults, cellvars, freevars,
                 lineno_table):

        self.name = name
        self.filepath = filepath
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts_w = consts
        self.defaults = defaults
        self.cellvars = cellvars
        self.freevars = freevars
        self.lineno_table = lineno_table

        n_args = len(args)
        arg_pos = [-1] * n_args
        for idx, arg in enumerate(args):
            arg_pos[idx] = cellvars.index(arg)
        self.arg_pos = arg_pos

        block_arg_pos = -1
        if block_arg is not None:
            block_arg_pos = cellvars.index(block_arg)
        self.block_arg_pos = block_arg_pos

        splat_arg_pos = -1
        if splat_arg is not None:
            splat_arg_pos = cellvars.index(splat_arg)
        self.splat_arg_pos = splat_arg_pos

    def __deepcopy__(self, memo):
        obj = super(W_CodeObject, self).__deepcopy__(memo)
        obj.name = self.name
        obj.filepath = self.filepath
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
        return obj

    @classdef.method("filepath")
    def method_filepath(self, space):
        return space.newstr_fromstr(self.filepath)
