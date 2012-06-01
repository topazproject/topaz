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

    moduledef.app_method("""
    def each_with_index
        i = 0
        self.each do |obj|
            yield obj, i
            i += 1
        end
    end
    """)

    moduledef.app_method("""
    def all?
        self.each do |obj|
            return false unless obj
        end
        return true
    end
    """)
