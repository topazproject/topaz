from pypy.rlib import jit

class ClassVariable(object):
    def __init__(self, name):
        self.name = name
        self.values = []
        self.modules = []

    def append(self, w_module, w_value):
        self.modules.append(w_module)
        self.values.append(w_value)

    def remove(self, w_module):
        idx = self.modules.index(w_module)
        self.modules.pop(idx)
        self.values.pop(idx)

class ClassVariables(object):
    def __init__(self):
        self.values = {}

    def get(self, space, w_module, name):
        cvar_with_idx = self._access_variable(space, w_module, name)
        if cvar_with_idx == None or len(cvar_with_idx) == 1:
            return None
        else:
            return cvar_with_idx[0].values[cvar_with_idx[1]]

    def set(self, space, w_module, name, w_value):
        cvar_with_idx = self._access_variable(space, w_module, name)
        if cvar_with_idx == None:
            cvar = ClassVariable(name)
            self.values[name] = cvar
            cvar.append(w_module, w_value)
        elif len(cvar_with_idx) == 1:
            cvar = cvar_with_idx[0]
            cvar_modules = cvar.modules + []
            # remove any subclasses' own version of the cvar
            for m in cvar_modules:
                if w_module.name in m.ancestors():
                    cvar.remove(m)
            cvar.append(w_module, w_value)
        else:
            cvar_with_idx[0].values[cvar_with_idx[1]] = w_value

    def _access_variable(self, space, w_module, name):
        variable = self.values.get(name, None)
        if variable == None:
            return None
        else:
            ancestors = w_module.ancestors()
            ancestors.reverse()
            module_names = [m.name for m in variable.modules]
            for m in ancestors:
                if m in module_names:
                    return [variable, module_names.index(m)]
            return [variable]
