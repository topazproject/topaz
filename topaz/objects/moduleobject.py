import copy

from rpython.rlib import jit

from topaz.celldict import CellDict, VersionTag
from topaz.module import ClassDef
from topaz.objects.functionobject import W_FunctionObject
from topaz.objects.objectobject import W_RootObject
from topaz.objects.procobject import W_ProcObject
from topaz.scope import StaticScope


class AttributeReader(W_FunctionObject):
    _immutable_fields_ = ["varname"]

    def __init__(self, varname):
        self.varname = varname

    def call(self, space, w_obj, args_w, block):
        return space.find_instance_var(w_obj, self.varname)


class AttributeWriter(W_FunctionObject):
    _immutable_fields_ = ["varname"]

    def __init__(self, varname):
        self.varname = varname

    def call(self, space, w_obj, args_w, block):
        [w_value] = args_w
        space.set_instance_var(w_obj, self.varname, w_value)
        return w_value

    def arity(self, space):
        return space.newint(1)


class UndefMethod(W_FunctionObject):
    _immutable_fields_ = ["name"]

    def __init__(self, name):
        self.name = name

    def call(self, space, w_obj, args_w, block):
        args_w.insert(0, space.newsymbol(self.name))
        return space.send(w_obj, space.newsymbol("method_missing"), args_w, block)


class DefineMethodBlock(W_FunctionObject):
    _immutable_fields_ = ["name", "block"]

    def __init__(self, name, block):
        self.name = name
        self.block = block

    def call(self, space, w_obj, args_w, block):
        method_block = self.block.copy(space, w_self=w_obj)
        return space.invoke_block(method_block, args_w, block)

    def arity(self, space):
        args_count = len(self.block.bytecode.arg_pos) - len(self.block.bytecode.defaults)
        if len(self.block.bytecode.defaults) > 0 or self.block.bytecode.splat_arg_pos != -1:
            args_count = -(args_count + 1)

        return space.newint(args_count)


class DefineMethodMethod(W_FunctionObject):
    _immutable_fields_ = ["name", "w_unbound_method"]

    def __init__(self, name, w_unbound_method):
        self.name = name
        self.w_unbound_method = w_unbound_method

    def call(self, space, w_obj, args_w, block):
        w_bound_method = space.send(self.w_unbound_method, space.newsymbol("bind"), [w_obj])
        return space.send(w_bound_method, space.newsymbol("call"), args_w, block)


class W_ModuleObject(W_RootObject):
    _immutable_fields_ = ["version?", "included_modules?[*]", "klass?", "name?"]

    classdef = ClassDef("Module", W_RootObject.classdef, filepath=__file__)

    def __init__(self, space, name):
        self.name = name
        self.klass = None
        self.version = VersionTag()
        self.methods_w = {}
        self.constants_w = {}
        self.class_variables = CellDict()
        self.instance_variables = CellDict()
        self.flags = CellDict()
        self.included_modules = []
        self.descendants = []

    def __deepcopy__(self, memo):
        obj = super(W_ModuleObject, self).__deepcopy__(memo)
        obj.name = self.name
        obj.klass = copy.deepcopy(self.klass, memo)
        obj.version = copy.deepcopy(self.version, memo)
        obj.methods_w = copy.deepcopy(self.methods_w, memo)
        obj.constants_w = copy.deepcopy(self.constants_w, memo)
        obj.class_variables = copy.deepcopy(self.class_variables, memo)
        obj.instance_variables = copy.deepcopy(self.instance_variables, memo)
        obj.included_modules = copy.deepcopy(self.included_modules, memo)
        obj.descendants = copy.deepcopy(self.descendants, memo)
        return obj

    def getclass(self, space):
        if self.klass is not None:
            return jit.promote(self).klass
        return W_RootObject.getclass(self, space)

    def getsingletonclass(self, space):
        if self.klass is None:
            self.klass = space.newclass(
                "#<Class:%s>" % self.name, space.w_module, is_singleton=True
            )
        return self.klass

    def mutated(self):
        self.version = VersionTag()

    def define_method(self, space, name, method):
        self.mutated()
        self.methods_w[name] = method

    @jit.unroll_safe
    def find_method(self, space, name):
        method = self._find_method_pure(space, name, self.version)
        if method is None:
            for module in self.included_modules:
                method = module.find_method(space, name)
                if method is not None:
                    return method
        return method

    @jit.unroll_safe
    def find_method_super(self, space, name):
        for module in self.included_modules:
            method = module.find_method(space, name)
            if method is not None:
                return method
        return None

    @jit.elidable
    def _find_method_pure(self, space, method, version):
        return self.methods_w.get(method, None)

    def set_const(self, space, name, w_obj):
        self.mutated()
        self.constants_w[name] = w_obj

    def find_const(self, space, name):
        w_res = self.find_included_const(space, name)
        if w_res is None:
            return space.w_object.find_const(space, name)
        else:
            return w_res

    @jit.unroll_safe
    def find_included_const(self, space, name):
        w_res = self.find_local_const(space, name)
        if w_res is None:
            for w_mod in self.included_modules:
                w_res = w_mod.find_local_const(space, name)
                if w_res is not None:
                    break
        return w_res

    def find_local_const(self, space, name):
        return self._find_const_pure(name, self.version)

    @jit.elidable
    def _find_const_pure(self, name, version):
        return self.constants_w.get(name, None)

    @jit.unroll_safe
    def set_class_var(self, space, name, w_obj):
        ancestors = self.ancestors()
        for idx in xrange(len(ancestors) - 1, -1, -1):
            module = ancestors[idx]
            assert isinstance(module, W_ModuleObject)
            w_res = module.class_variables.get(space, name)
            if w_res is not None or module is self:
                module.class_variables.set(space, name, w_obj)
                if module is self:
                    for descendant in self.descendants:
                        descendant.remove_class_var(space, name)

    @jit.unroll_safe
    def find_class_var(self, space, name):
        w_res = self.class_variables.get(space, name)
        if w_res is None:
            ancestors = self.ancestors()
            for idx in xrange(1, len(ancestors)):
                module = ancestors[idx]
                assert isinstance(module, W_ModuleObject)
                w_res = module.class_variables.get(space, name)
                if w_res is not None:
                    break
        return w_res

    @jit.unroll_safe
    def remove_class_var(self, space, name):
        self.class_variables.delete(name)
        for descendant in self.descendants:
            descendant.remove_class_var(space, name)

    def set_instance_var(self, space, name, w_value):
        return self.instance_variables.set(space, name, w_value)

    def find_instance_var(self, space, name):
        return self.instance_variables.get(space, name) or space.w_nil

    def copy_instance_vars(self, space, w_other):
        assert isinstance(w_other, W_ModuleObject)
        for key in w_other.instance_variables:
            w_value = w_other.instance_variables.get(space, key)
            self.set_instance_var(space, key, w_value)

    def set_flag(self, space, name):
        self.flags.set(space, name, space.w_true)

    def unset_flag(self, space, name):
        self.flags.set(space, name, space.w_false)

    def copy_flags(self, space, w_other):
        assert isinstance(w_other, W_ModuleObject)
        for key in w_other.flags:
            w_value = w_other.flags.get(space, key)
            if w_value is space.w_true:
                self.set_flag(space, key)

    def ancestors(self, include_singleton=True, include_self=True):
        if include_self:
            return [self] + self.included_modules
        else:
            return self.included_modules[:]

    @jit.unroll_safe
    def is_ancestor_of(self, w_cls):
        if self is w_cls:
            return True
        for w_mod in w_cls.included_modules:
            if self is w_mod:
                return True
        if w_cls.superclass is not None:
            return self.is_ancestor_of(w_cls.superclass)
        return False

    def include_module(self, space, w_mod):
        assert isinstance(w_mod, W_ModuleObject)
        if w_mod not in self.ancestors():
            self.included_modules = [w_mod] + self.included_modules
            w_mod.included(space, self)

    def included(self, space, w_mod):
        self.descendants.append(w_mod)
        if space.respond_to(self, space.newsymbol("included")):
            space.send(self, space.newsymbol("included"), [w_mod])

    def extend_object(self, space, w_obj, w_mod):
        if w_mod not in self.ancestors():
            self.included_modules = [w_mod] + self.included_modules
            w_mod.extended(space, w_obj, self)

    def extended(self, space, w_obj, w_mod):
        self.descendants.append(w_mod)
        if space.respond_to(self, space.newsymbol("extended")):
            space.send(self, space.newsymbol("extended"), [w_obj])

    def set_visibility(self, space, names_w, visibility):
        names = [space.symbol_w(w_name) for w_name in names_w]
        if names:
            for name in names:
                self.set_method_visibility(space, name, visibility)
        else:
            self.set_default_visibility(space, visibility)

    def set_default_visibility(self, space, visibility):
        pass

    def set_method_visibility(self, space, name, visibility):
        pass

    @classdef.singleton_method("nesting")
    def singleton_method_nesting(self, space):
        frame = space.getexecutioncontext().gettoprubyframe()
        modules_w = []
        scope = frame.lexical_scope
        while scope is not None:
            modules_w.append(scope.w_mod)
            scope = scope.backscope
        return space.newarray(modules_w)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_ModuleObject(space, None)

    @classdef.method("to_s")
    def method_to_s(self, space):
        name = self.name
        if name is None:
            return space.newstr_fromstr(space.any_to_s(self))
        return space.newstr_fromstr(name)

    @classdef.method("include")
    def method_include(self, space, w_mod):
        space.send(w_mod, space.newsymbol("append_features"), [self])

    @classdef.method("append_features")
    def method_append_features(self, space, w_mod):
        ancestors = self.ancestors()
        for idx in xrange(len(ancestors) - 1, -1, -1):
            w_mod.include_module(space, ancestors[idx])

    @classdef.method("define_method", name="symbol")
    def method_define_method(self, space, name, w_method=None, block=None):
        if w_method is not None:
            if space.is_kind_of(w_method, space.w_method):
                w_method = space.send(w_method, space.newsymbol("unbind"))

            if space.is_kind_of(w_method, space.w_unbound_method):
                self.define_method(space, name, DefineMethodMethod(name, w_method))
            elif space.is_kind_of(w_method, space.w_proc):
                assert isinstance(w_method, W_ProcObject)
                self.define_method(space, name, DefineMethodBlock(name, w_method))
        elif block is not None:
            self.define_method(space, name, DefineMethodBlock(name, block))
        else:
            raise space.error(space.w_ArgumentError, "tried to create Proc object without a block")

    @classdef.method("attr_accessor")
    def method_attr_accessor(self, space, args_w):
        self.method_attr_reader(space, args_w)
        self.method_attr_writer(space, args_w)

    @classdef.method("attr_reader")
    def method_attr_reader(self, space, args_w):
        for w_arg in args_w:
            varname = space.symbol_w(w_arg)
            self.define_method(space, varname, AttributeReader("@" + varname))

    @classdef.method("attr_writer")
    def method_attr_writer(self, space, args_w):
        for w_arg in args_w:
            varname = space.symbol_w(w_arg)
            self.define_method(space, varname + "=", AttributeWriter("@" + varname))

    @classdef.method("attr")
    def method_attr(self, space, args_w):
        if len(args_w) == 2 and (args_w[1] is space.w_true or args_w[1] is space.w_false):
            [w_name, w_writable] = args_w
            if space.is_true(w_writable):
                self.method_attr_accessor(space, [w_name])
            else:
                self.method_attr_reader(space, [w_name])
        else:
            self.method_attr_reader(space, args_w)

    @classdef.method("module_function")
    def method_module_function(self, space, args_w):
        for w_arg in args_w:
            name = space.symbol_w(w_arg)
            self.attach_method(space, name, self._find_method_pure(space, name, self.version))

    @classdef.method("private_class_method")
    def method_private_class_method(self, space, w_name):
        w_cls = self.getsingletonclass(space)
        return space.send(w_cls, space.newsymbol("private"), [w_name])

    @classdef.method("public_class_method")
    def method_public_class_method(self, space, w_name):
        w_cls = self.getsingletonclass(space)
        return space.send(w_cls, space.newsymbol("public"), [w_name])

    @classdef.method("alias_method", new_name="symbol", old_name="symbol")
    def method_alias_method(self, space, new_name, old_name):
        self.define_method(space, new_name, self.find_method(space, old_name))

    @classdef.method("ancestors")
    def method_ancestors(self, space):
        return space.newarray(self.ancestors(include_singleton=False))

    @classdef.method("included")
    def method_included(self, space, w_mod):
        # TODO: should be private
        pass

    @classdef.method("extended")
    def method_extended(self, space, w_mod):
        # TODO: should be private
        pass

    @classdef.method("name")
    def method_name(self, space):
        if self.name is None:
            return space.w_nil
        return space.newstr_fromstr(self.name)

    @classdef.method("private")
    def method_private(self, space, args_w):
        self.set_visibility(space, args_w, "private")

    @classdef.method("public")
    def method_public(self, space, args_w):
        self.set_visibility(space, args_w, "public")

    @classdef.method("protected")
    def method_protected(self, space, args_w):
        self.set_visibility(space, args_w, "protected")

    @classdef.method("private_constant")
    def method_private_constant(self, space, args_w):
        pass

    @classdef.method("constants")
    def method_constants(self, space):
        return space.newarray([space.newsymbol(n) for n in self.constants_w])

    @classdef.method("const_missing", name="symbol")
    def method_const_missing(self, space, name):
        raise space.error(space.w_NameError, "uninitialized constant %s" % name)

    @classdef.method("class_eval", string="str", filename="str")
    @classdef.method("module_eval", string="str", filename="str")
    def method_module_eval(self, space, string=None, filename=None, w_lineno=None, block=None):
        if string is not None:
            if filename is None:
                filename = "module_eval"
            if w_lineno is not None:
                lineno = space.int_w(w_lineno)
            else:
                lineno = 1
            return space.execute(string, self, lexical_scope=StaticScope(self, None), filepath=filename, initial_lineno=lineno)
        elif block is None:
            raise space.error(space.w_ArgumentError, "block not supplied")
        else:
            space.invoke_block(block.copy(space, w_self=self, lexical_scope=StaticScope(self, block.lexical_scope)), [])

    @classdef.method("const_defined?", const="str", inherit="bool")
    def method_const_definedp(self, space, const, inherit=True):
        if inherit:
            return space.newbool(self.find_const(space, const) is not None)
        else:
            return space.newbool(self.find_local_const(space, const) is not None)

    @classdef.method("const_get", const="symbol", inherit="bool")
    def method_const_get(self, space, const, inherit=True):
        if inherit:
            w_res = self.find_const(space, const)
        else:
            w_res = self.find_local_const(space, const)
        if w_res is None:
            name = space.obj_to_s(self)
            raise space.error(space.w_NameError,
                "uninitialized constant %s::%s" % (name, const)
            )
        return w_res

    @classdef.method("const_set", const="symbol")
    def method_const_set(self, space, const, w_value):
        space.set_const(self, const, w_value)
        return w_value

    @classdef.method("class_variable_defined?", name="symbol")
    def method_class_variable_definedp(self, space, name):
        return space.newbool(self.find_class_var(space, name) is not None)

    @classdef.method("remove_class_variable", name="symbol")
    def method_remove_class_variable(self, space, name):
        w_value = self.class_variables.get(space, name)
        if w_value is not None:
            self.class_variables.delete(name)
            return w_value
        if self.find_class_var(space, name) is not None:
            raise space.error(space.w_NameError,
                "cannot remove %s for %s" % (name, space.obj_to_s(self))
            )
        raise space.error(space.w_NameError,
            "class variable %s not defined for %s" % (name, space.obj_to_s(self))
        )

    @classdef.method("method_defined?", name="str")
    def method_method_definedp(self, space, name):
        return space.newbool(self.find_method(space, name) is not None)

    @classdef.method("===")
    def method_eqeqeq(self, space, w_obj):
        return space.newbool(self.is_ancestor_of(space.getclass(w_obj)))

    @classdef.method("instance_method", name="symbol")
    def method_instance_method(self, space, name):
        return space.newmethod(name, self)

    @classdef.method("undef_method", name="symbol")
    def method_undef_method(self, space, name):
        w_method = self.find_method(space, name)
        if w_method is None or isinstance(w_method, UndefMethod):
            cls_name = space.obj_to_s(self)
            raise space.error(space.w_NameError,
                "undefined method `%s' for class `%s'" % (name, cls_name)
            )
        self.define_method(space, name, UndefMethod(name))
        return self

    @classdef.method("remove_method", name="symbol")
    def method_remove_method(self, space, name):
        w_method = self._find_method_pure(space, name, self.version)
        if w_method is None or isinstance(w_method, UndefMethod):
            cls_name = space.obj_to_s(self)
            raise space.error(space.w_NameError,
                "method `%s' not defined in %s" % (name, cls_name)
            )
        self.define_method(space, name, UndefMethod(name))
        return self
