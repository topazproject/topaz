import copy

from rpython.rlib.objectmodel import specialize

from topaz.module import ClassDef
from topaz.objects.moduleobject import UndefMethod, W_ModuleObject
from topaz.objects.objectobject import W_Object


class W_ClassObject(W_ModuleObject):
    _immutable_fields_ = ["superclass?", "is_singleton"]

    classdef = ClassDef("Class", W_ModuleObject.classdef)

    def __init__(self, space, name, superclass, is_singleton=False, attached=None):
        W_ModuleObject.__init__(self, space, name)
        self.superclass = superclass
        self.is_singleton = is_singleton
        self.attached = attached

        if self.superclass is not None:
            self.superclass.inherited(space, self)
            # During bootstrap, we cannot create singleton classes, yet
            if not self.is_singleton and not space.bootstrap:
                self.getsingletonclass(space)

    def __deepcopy__(self, memo):
        obj = super(W_ClassObject, self).__deepcopy__(memo)
        obj.is_singleton = self.is_singleton
        obj.attached = copy.deepcopy(self.attached, memo)
        obj.superclass = copy.deepcopy(self.superclass, memo)
        return obj

    def getsingletonclass(self, space):
        if self.klass is None or not self.klass.is_singleton:
            if self.superclass is None:
                singleton_superclass = space.w_class
            else:
                singleton_superclass = self.superclass.getsingletonclass(space)
            if self.name is None:
                name = None
            else:
                name = "#<Class:%s>" % self.name
            self.klass = space.newclass(
                name, singleton_superclass, is_singleton=True, attached=self
            )
        return self.klass

    def find_const(self, space, name, autoload=True):
        w_res = W_ModuleObject.find_included_const(self, space, name, autoload=autoload)
        if w_res is None and self.superclass is not None:
            w_res = self.superclass.find_const(space, name, autoload=autoload)
        return w_res

    def inherited_constants(self, space):
        consts = {}
        for const in W_ModuleObject.local_constants(self, space):
            consts[const] = None
        w_cls = self.superclass
        while w_cls is not None:
            for const in w_cls.local_constants(space):
                consts[const] = None
            w_cls = w_cls.superclass

        return consts.keys()

    def find_method(self, space, name):
        method = W_ModuleObject.find_method(self, space, name)
        if method is None and self.superclass is not None:
            method = self.superclass.find_method(space, name)
        return method

    def find_method_super(self, space, name):
        method = W_ModuleObject.find_method_super(self, space, name)
        if method is None and self.superclass is not None:
            method = self.superclass.find_method(space, name)
        return method

    @specialize.argtype(2)
    def methods(self, space, visibility=None, inherit=True):
        methods = {}
        for name in W_ModuleObject.methods(self, space, inherit=inherit, visibility=visibility):
            methods[name] = None
        if inherit and self.superclass is not None:
            for name in self.superclass.methods(space, visibility=visibility):
                method = self._find_method_pure(space, name, self.version)
                if method is None or not isinstance(method, UndefMethod):
                    methods[name] = None
        return methods.keys()

    def ancestors(self, include_singleton=True, include_self=True):
        assert include_self
        ary = W_ModuleObject.ancestors(self,
            include_singleton, not (self.is_singleton and not include_singleton)
        )
        if self.superclass is not None:
            ary += self.superclass.ancestors(include_singleton)
        return ary

    def inherited(self, space, w_mod):
        self.descendants.append(w_mod)
        if not space.bootstrap and space.respond_to(self, "inherited"):
            space.send(self, "inherited", [w_mod])

    def method_removed(self, space, w_name):
        if self.is_singleton:
            space.send(self.attached, "singleton_method_removed", [w_name])
        else:
            W_ModuleObject.method_removed(self, space, w_name)

    def method_added(self, space, w_name):
        if self.is_singleton:
            space.send(self.attached, "singleton_method_added", [w_name])
        else:
            W_ModuleObject.method_added(self, space, w_name)

    def method_undefined(self, space, w_name):
        if self.is_singleton:
            space.send(self.attached, "singleton_method_undefined", [w_name])
        else:
            W_ModuleObject.method_undefined(self, space, w_name)

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space):
        return space.newclass(None, None)

    @classdef.method("new")
    def method_new(self, space, args_w, block):
        w_obj = space.send(self, "allocate")
        space.send(w_obj, "initialize", args_w, block)
        return w_obj

    @classdef.method("allocate")
    def method_allocate(self, space):
        return W_Object(space, self)

    @classdef.method("initialize")
    def method_initialize(self, space, w_superclass=None, block=None):
        if self.superclass is not None or self is space.w_basicobject:
            raise space.error(space.w_TypeError, "already initialized class")
        if w_superclass is not None:
            if not isinstance(w_superclass, W_ClassObject):
                raise space.error(space.w_TypeError,
                    "superclass must be a Class (%s given)" % space.obj_to_s(space.getclass(w_superclass))
                )
            if w_superclass is space.w_class:
                raise space.error(space.w_TypeError,
                    "can't make subclass of Class"
                )
            if w_superclass.is_singleton:
                raise space.error(space.w_TypeError,
                    "can't make subclass of singleton class"
                )
        else:
            w_superclass = space.w_object
        self.superclass = w_superclass
        self.superclass.inherited(space, self)
        self.getsingletonclass(space)
        space.send_super(space.getclassfor(W_ClassObject), self, "initialize", [], block=block)

    @classdef.method("initialize_copy")
    def method_initialize_copy(self, space, w_other):
        if self.superclass is not None or self is space.w_basicobject:
            raise space.error(space.w_TypeError, "already initialized class")
        return space.send_super(space.getclassfor(W_ClassObject), self, "initialize_copy", [w_other])

    @classdef.method("superclass")
    def method_superclass(self, space):
        if self.superclass is not None:
            return self.superclass
        if self is space.w_basicobject:
            return space.w_nil
        raise space.error(space.w_TypeError, "uninitialized class")

    @classdef.method("class_variables")
    def method_class_variables(self, space):
        return space.newarray([space.newsymbol(cvar) for cvar in self.class_variables])

    @classdef.method("instance_variables")
    def method_instance_variables(self, space):
        return space.newarray([space.newsymbol(ivar) for ivar in self.instance_variables])
