from rupypy.module import Module, ModuleDef


class Enumerable(Module):
    moduledef = ModuleDef("Enumerable")

    moduledef.app_method("""
    def map
        result = []
        self.each do |x|
            result << (yield x)
        end
        result
    end
    """)

    moduledef.app_method("""
    def inject memo
        self.each do |x|
            memo = (yield memo, x)
        end
        memo
    end
    """)
