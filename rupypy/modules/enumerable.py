from rupypy.module import Module, ModuleDef


class Enumerable(Module):
    moduledef = ModuleDef("Enumerable")

    moduledef.app_function("""
    def map
        result = []
        self.each do |x|
            result << (yield x)
        end
        result
    end
    """)
