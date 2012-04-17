from rupypy.module import ClassDef, BaseFunction
from rupypy.objects.objectobject import W_BaseObject


class AttributeReader(BaseFunction):
    _immutable_fields_ = ["varname"]
    def __init__(self, varname):
        self.varname = varname

    def call(self, space, w_obj, args_w, block):
        return space.find_instance_var(w_obj, self.varname)

class W_ModuleObject(W_BaseObject):
    classdef = ClassDef("Module", W_BaseObject.classdef)

    @classdef.method("attr_accessor", varname="symbol")
    def method_attr_accessor(self, space, varname):
        self.add_method(space, varname, AttributeReader(varname))
