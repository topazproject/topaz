from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.functionobject import W_FunctionObject
from rupypy.objects.objectobject import W_RootObject
from rupypy.objects.exceptionobject import W_NameError


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


class VersionTag(object):
    pass


class W_ModuleObject(W_RootObject):
    _immutable_fields_ = [
        "version?", "included_modules?[*]", "lexical_scope?", "klass?"
    ]

    classdef = ClassDef("Module", W_RootObject.classdef)

    def __init__(self, space, name, superclass):
        from rupypy.celldict import CellDict

        self.name = name
        self.klass = None
        self.superclass = superclass
        self.version = VersionTag()
        self.methods_w = {}
        self.constants_w = {}
        self.class_variables = CellDict()
        self.instance_variables = CellDict()
        self.lexical_scope = None
        self.included_modules = []
        self.descendants = []

    def getclass(self, space):
        if self.klass is not None:
            return self.klass
        return W_RootObject.getclass(self, space)

    def getsingletonclass(self, space):
        if self.klass is None:
            self.klass = space.newclass(
                "#<Class:%s>" % self.name, space.getclassfor(W_ModuleObject), is_singleton=True
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

    @jit.elidable
    def _find_method_pure(self, space, method, version):
        return self.methods_w.get(method, None)

    def set_lexical_scope(self, space, w_mod):
        self.lexical_scope = w_mod

    def set_const(self, space, name, w_obj):
        self.mutated()
        self.constants_w[name] = w_obj

    def find_const(self, space, name):
        res = self._find_const_pure(name, self.version)
        if res is None and self.lexical_scope is not None:
            res = self.lexical_scope.find_lexical_const(space, name)
        if res is None and self.superclass is not None:
            res = self.superclass.find_inherited_const(space, name)
        return res

    def find_lexical_const(self, space, name):
        res = self._find_const_pure(name, self.version)
        if res is None and self.lexical_scope is not None:
            return self.lexical_scope.find_lexical_const(space, name)
        return res

    def find_inherited_const(self, space, name):
        res = self._find_const_pure(name, self.version)
        if res is None and self.superclass is not None:
            return self.superclass.find_inherited_const(space, name)
        return res

    @jit.elidable
    def _find_const_pure(self, name, version):
        return self.constants_w.get(name, None)

    @jit.unroll_safe
    def set_class_var(self, space, name, w_obj):
        ancestors = self.ancestors()
        for idx in xrange(len(ancestors) - 1, -1, -1):
            module = ancestors[idx]
            assert isinstance(module, W_ModuleObject)
            w_res = module.class_variables.get(name)
            if w_res is not None or module is self:
                module.class_variables.set(name, w_obj)
                if module is self:
                    for descendant in self.descendants:
                        descendant.remove_class_var(space, name)

    @jit.unroll_safe
    def find_class_var(self, space, name):
        w_res = self.class_variables.get(name)
        if w_res is None:
            ancestors = self.ancestors()
            for idx in xrange(1, len(ancestors)):
                module = ancestors[idx]
                assert isinstance(module, W_ModuleObject)
                w_res = module.class_variables.get(name)
                if w_res is not None:
                    break
        return w_res

    @jit.unroll_safe
    def remove_class_var(self, space, name):
        self.class_variables.delete(name)
        for descendant in self.descendants:
            descendant.remove_class_var(space, name)

    def set_instance_var(self, space, name, w_value):
        return self.instance_variables.set(name, w_value)

    def find_instance_var(self, space, name):
        return self.instance_variables.get(name) or space.w_nil

    def ancestors(self, include_singleton=True, include_self=True):
        if include_self:
            return [self] + self.included_modules
        else:
            return self.included_modules[:]

    def is_ancestor_of(self, w_cls):
        if self is w_cls or self in w_cls.included_modules:
            return True
        elif w_cls.superclass is not None:
            return self.is_ancestor_of(w_cls.superclass)
        else:
            return False

    def include_module(self, space, w_mod):
        assert isinstance(w_mod, W_ModuleObject)
        if w_mod not in self.ancestors():
            self.included_modules = [w_mod] + self.included_modules
            w_mod.included(space, self)

    def included(self, space, w_mod):
        self.descendants.append(w_mod)
        space.send(self, space.newsymbol("included"), [w_mod])

    def inherited(self, space, w_mod):
        self.descendants.append(w_mod)
        if not space.bootstrap:
            space.send(self, space.newsymbol("inherited"), [w_mod])

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

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.name)

    @classdef.method("include")
    def method_include(self, space, w_mod):
        space.send(w_mod, space.newsymbol("append_features"), [self])

    @classdef.method("append_features")
    def method_append_features(self, space, w_mod):
        ancestors = self.ancestors()
        for idx in xrange(len(ancestors) - 1, -1, -1):
            w_mod.include_module(space, ancestors[idx])

    @classdef.method("attr_accessor")
    def method_attr_accessor(self, space, args_w):
        self.method_attr_reader(space, args_w)
        for w_arg in args_w:
            varname = space.symbol_w(w_arg)
            self.define_method(space, varname + "=", AttributeWriter("@" + varname))

    @classdef.method("attr_reader")
    def method_attr_reader(self, space, args_w):
        for w_arg in args_w:
            varname = space.symbol_w(w_arg)
            self.define_method(space, varname, AttributeReader("@" + varname))

    @classdef.method("module_function", name="symbol")
    def method_module_function(self, space, name):
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

    @classdef.method("inherited")
    def method_inherited(self, space, w_mod):
        pass

    @classdef.method("included")
    def method_included(self, space, w_mod):
        pass

    @classdef.method("name")
    def method_name(self, space):
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

    @classdef.method("constants")
    def method_constants(self, space):
        return space.newarray([space.newsymbol(n) for n in self.constants_w])

    @classdef.method("const_missing", name="symbol")
    def method_const_missing(self, space, name):
        raise space.error(space.getclassfor(W_NameError),
             "uninitialized constant %s" % name
        )

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
            return space.execute(string, self, self, filename, lineno)
        else:
            space.invoke_block(block.copy(w_self=self, w_scope=self), [])

    @classdef.method("const_defined?", const="str", inherit="bool")
    def method_const_definedp(self, space, const, inherit=True):
        if inherit:
            return space.newbool(self.find_inherited_const(space, const) is not None)
        else:
            return space.newbool(self._find_const_pure(const, self.version) is not None)

    @classdef.method("method_defined?", name="str")
    def method_method_definedp(self, space, name):
        return space.newbool(self.find_method(space, name) is not None)

    @classdef.method("===")
    def method_eqeqeq(self, space, w_obj):
        return space.newbool(self.is_ancestor_of(space.getclass(w_obj)))
