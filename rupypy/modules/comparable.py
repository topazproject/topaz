from rupypy.module import Module, ModuleDef

class Comparable(Module):
    moduledef = ModuleDef("Comparable")

    moduledef.app_method("""
    def < other
        if self < other
            return true
        end
        return false
    end
    """)

    moduledef.app_method("""
    def > other
        if self > other
            return true
        end
        return false
    end
    """)

    # moduledef.app_method("""
    # def <= other
    #     if self < other
    #         return true
    #     elsif self == other
    #         return true
    #     end
    #     return false
    # end
    # """)
>>>>>>> Add < and > to Comparable
