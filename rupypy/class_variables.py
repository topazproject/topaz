from pypy.rlib import jit

class ClassVariable(object):
    def __init__(self, name):
        self.name = name
        self.values = []
        self.modules = []

    def append(self, w_module, w_value):
        self.modules.append(w_module)
        self.values.append(ClassVariableValue(w_value))

    def remove(self, w_module):
        idx = self.modules.index(w_module)
        self.modules.pop(idx)
        self.values.pop(idx)

    @jit.elidable
    def get_value(self, space, w_module):
        ancestors = w_module.ancestors()
        ancestors.reverse()
        module_names = [m.name for m in self.modules]
        for module_name in ancestors:
            if module_name in module_names:
                idx = module_names.index(module_name)
                return self.values[idx]
        return None

class ClassVariableValue(object):
    def __init__(self, w_value):
        self.w_value = w_value

class ClassVariables(object):
    def __init__(self):
        self.cvars = {}

    def get(self, space, w_module, name):
        cvar = self.cvars.get(name, None)
        if cvar is not None:
            value = cvar.get_value(space, w_module)
            if value is not None:
                return value.w_value
        return None

    def set(self, space, w_module, name, w_value):
        cvar = self.cvars.get(name, None)
        if cvar is None:
            cvar = ClassVariable(name)
            self.cvars[name] = cvar
            cvar.append(w_module, w_value)
        else:
            value = cvar.get_value(space, w_module)
            if value is None:
                cvar_modules = cvar.modules + []
                # remove any subclasses' own version of the cvar
                for w_m in cvar_modules:
                    if w_module.name in w_m.ancestors():
                        cvar.remove(w_m)
                cvar.append(w_module, w_value)
            else:
                value.w_value = w_value
