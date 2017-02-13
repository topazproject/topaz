from rpython.rlib import jit

from topaz.coerce import Coerce
from topaz.closure import LocalCell
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.hashobject import W_HashObject
from topaz.objects.functionobject import W_FunctionObject


class BaseFrame(object):
    _attrs_ = ["backref", "escaped", "back_last_instr"]

    def __init__(self):
        self.backref = jit.vref_None
        self.escaped = False


class Frame(BaseFrame):
    _virtualizable_ = [
        "bytecode", "localsstack_w[*]", "stackpos", "w_self", "block",
        "cells[*]", "lastblock", "lexical_scope", "last_instr", "parent_interp",
        "top_parent_interp",
    ]

    @jit.unroll_safe
    def __init__(self, bytecode, w_self, lexical_scope, block, parent_interp,
                 top_parent_interp, regexp_match_cell):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        BaseFrame.__init__(self)
        self.bytecode = bytecode
        self.localsstack_w = [None] * (len(bytecode.cellvars) + bytecode.max_stackdepth)
        self.stackpos = len(bytecode.cellvars)
        self.last_instr = 0
        self.cells = [LocalCell() for _ in bytecode.cellvars] + [None] * len(bytecode.freevars)
        self.regexp_match_cell = regexp_match_cell
        self.w_self = w_self
        self.lexical_scope = lexical_scope
        self.block = block
        self.parent_interp = parent_interp
        self.top_parent_interp = top_parent_interp
        self.visibility = W_FunctionObject.PUBLIC
        self.lastblock = None

    def _set_arg(self, space, pos, w_value):
        assert pos >= 0
        self.cells[pos].set(space, self, pos, w_value)

    def handle_block_args(self, space, bytecode, args_w, block):
        if (len(args_w) == 1 and (
                len(bytecode.arg_pos) >= 2 or (
                    len(bytecode.arg_pos) > 0 and bytecode.splat_arg_pos != -1))):
            w_arg = args_w[0]
            if not space.is_kind_of(w_arg, space.w_array) and space.respond_to(w_arg, "to_ary"):
                w_arg = space.convert_type(w_arg, space.w_array, "to_ary", raise_error=True, reraise_error=True)
            if space.is_kind_of(w_arg, space.w_array):
                args_w = space.listview(w_arg)
        minargc = len(bytecode.arg_pos) - len(bytecode.defaults)
        if len(args_w) < minargc:
            args_w.extend([space.w_nil] * (minargc - len(args_w)))
        if bytecode.splat_arg_pos == -1:
            if len(args_w) > len(bytecode.arg_pos):
                del args_w[len(bytecode.arg_pos):]
        return self.handle_args(space, bytecode, args_w, block)

    @jit.unroll_safe
    def handle_args(self, space, bytecode, args_w, block):
        from topaz.interpreter import Interpreter

        keywords_hash = None
        if len(bytecode.kwarg_names) > 0 or bytecode.kwrest_pos != -1:
            # we only take the hash if we have more than enough arguments
            if len(args_w) > 0 and len(args_w) > (len(bytecode.arg_pos) - len(bytecode.defaults)):
                w_obj = args_w[-1]
                if not space.is_kind_of(w_obj, space.w_hash):
                    w_obj = space.convert_type(w_obj, space.w_hash, "to_hash", reraise_error=True)
                if isinstance(w_obj, W_HashObject):
                    keywords_hash = space.send(w_obj, "clone")
                    assert isinstance(keywords_hash, W_HashObject)

        if len(bytecode.kw_defaults) < len(bytecode.kwarg_names) and not keywords_hash:
            raise space.error(space.w_ArgumentError,
                "missing keywords: %s" % ",".join(bytecode.kwarg_names)
            )

        pre = 0
        post = len(args_w) if keywords_hash is None else len(args_w) - 1

        if (post < (len(bytecode.arg_pos) - len(bytecode.defaults)) or
            (bytecode.splat_arg_pos == -1 and post > len(bytecode.arg_pos))):
            raise space.error(space.w_ArgumentError,
                "wrong number of arguments (%d for %d)" % (len(args_w), len(bytecode.arg_pos) - len(bytecode.defaults))
            )

        if bytecode.default_arg_begin != -1:
            len_pre_args = bytecode.default_arg_begin
        elif bytecode.splat_arg_pos != -1:
            len_pre_args = bytecode.splat_arg_pos
        else:
            len_pre_args = len(bytecode.arg_pos)
        len_post_arg = len(bytecode.arg_pos) - len(bytecode.defaults) - len_pre_args

        # [required args, optional args, splat arg, required args, keywords args, keyword rest, block]
        #  ^                                                      ^
        # pre                                                   post

        # fill post-arguments from back.
        actual_args_len = post
        offset = len(bytecode.arg_pos) - post
        for i in xrange(actual_args_len - 1, actual_args_len - len_post_arg - 1, -1):
            self._set_arg(space, bytecode.arg_pos[i + offset], args_w[i])
            post -= 1
        # [required args, optional args, splat arg, required args, keywords args, keyword rest, block]
        #  ^                                       ^-------------
        # pre                                    post

        # fill arguments from start as far as we can (until we hit post or the
        # end of the default arguments + normal arguments
        for i in xrange(min(post, len_pre_args + len(bytecode.defaults))):
            self._set_arg(space, bytecode.arg_pos[i], args_w[i])
            pre += 1
        # [required args, optional args, splat arg, required args, keywords args, keyword rest, block]
        #  ------------------------^               ^
        #                         pre            post

        given_defaults = pre - len_pre_args
        # fill up remaining default arguments with their default values
        for i in xrange(given_defaults, len(bytecode.defaults)):
            bc = bytecode.defaults[i]
            self.bytecode = bc
            w_value = Interpreter().interpret(space, self, bc)
            self._set_arg(space, bytecode.arg_pos[len_pre_args + i], w_value)

        if bytecode.splat_arg_pos != -1:
            if pre >= post:
                splat_args_w = []
            else:
                splat_args_w = args_w[pre:post]
            w_splat_args = space.newarray(splat_args_w)
            self._set_arg(space, bytecode.splat_arg_pos, w_splat_args)

        for i, name in enumerate(bytecode.kwarg_names):
            w_key = space.newsymbol(name)
            w_value = None
            if keywords_hash is not None:
                try:
                    w_value = keywords_hash.getitem(w_key)
                    keywords_hash.delete(w_key)
                except KeyError:
                    pass
            # kword arguments with defaults come first, so if we get an
            # index error here, we're missing a required keyword argument
            if w_value is None:
                try:
                    bc = bytecode.kw_defaults[i]
                except IndexError:
                    raise space.error(space.w_ArgumentError,
                        "missing keyword: %s" % name
                    )
                self.bytecode = bc
                w_value = Interpreter().interpret(space, self, bc)
            self._set_arg(space, bytecode.cellvars.index(name), w_value)

        self.bytecode = bytecode

        if bytecode.kwrest_pos != -1:
            if keywords_hash is not None:
                self._set_arg(space, bytecode.kwrest_pos, keywords_hash)
            else:
                self._set_arg(space, bytecode.kwrest_pos, space.newhash())
        elif keywords_hash is not None:
            if keywords_hash.size() > 0:
                raise space.error(space.w_ArgumentError,
                    "unknown keywords: %s" % space.str_w(
                        space.send(space.send(keywords_hash, "keys"), "to_s")
                    )
                )

        if bytecode.block_arg_pos != -1:
            if block is None:
                w_block = space.w_nil
            else:
                w_block = block.copy(space)
            self._set_arg(space, bytecode.block_arg_pos, w_block)

    def push(self, w_obj):
        stackpos = jit.promote(self.stackpos)
        self.localsstack_w[stackpos] = w_obj
        self.stackpos = stackpos + 1

    def pop(self):
        stackpos = jit.promote(self.stackpos) - 1
        assert stackpos >= 0
        w_res = self.localsstack_w[stackpos]
        self.localsstack_w[stackpos] = None
        self.stackpos = stackpos
        return w_res

    @jit.unroll_safe
    def popitemsreverse(self, n):
        items_w = [None] * n
        for i in xrange(n - 1, -1, -1):
            items_w[i] = self.pop()
        return items_w

    def peek(self):
        stackpos = jit.promote(self.stackpos) - 1
        assert stackpos >= 0
        return self.localsstack_w[stackpos]

    def popblock(self):
        lastblock = self.lastblock
        if lastblock is not None:
            self.lastblock = lastblock.lastblock
        return lastblock

    @jit.unroll_safe
    def unrollstack(self, kind):
        while self.lastblock is not None:
            block = self.popblock()
            if block.handling_mask & kind:
                return block
            block.cleanupstack(self)

    def unrollstack_and_jump(self, space, unroller):
        block = self.unrollstack(unroller.kind)
        return block.handle(space, self, unroller)

    def has_contents(self):
        return True

    def get_filename(self):
        return self.bytecode.filepath

    def get_lineno(self, prev_frame):
        if prev_frame is None:
            instr = self.last_instr
        else:
            instr = prev_frame.back_last_instr - 1
        try:
            return self.bytecode.lineno_table[instr]
        except IndexError:
            return self.last_instr

    def get_code_name(self):
        return self.bytecode.name


class BuiltinFrame(BaseFrame):
    def __init__(self, name):
        BaseFrame.__init__(self)
        self.name = name

    def has_contents(self):
        return self.backref() is not None

    def get_filename(self):
        return self.backref().get_filename()

    def get_lineno(self, prev_frame):
        return self.backref().get_lineno(self)

    def get_code_name(self):
        return self.name
