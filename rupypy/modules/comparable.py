from rupypy.module import Module, ModuleDef


class Comparable(Module):
    moduledef = ModuleDef("Comparable")

    moduledef.app_method("""
    def > other
        return (self <=> other) > 0
    end
    """)

    moduledef.app_method("""
    def < other
        return (self <=> other) < 0
    end
    """)

    moduledef.app_method("""
    def >= other
        return !((self <=> other) < 0)
    end
    """)

    moduledef.app_method("""
    def <= other
        return !((self <=> other) > 0)
    end
    """)

    moduledef.app_method("""
    def == other
        return (self <=> other) == 0
    end
    """)

    moduledef.app_method("""
    def between? min, max
        return self > min && self < max
    end
    """)
