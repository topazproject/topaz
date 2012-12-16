from rupypy.module import Module, ModuleDef


class Comparable(Module):
    moduledef = ModuleDef("Comparable", filepath=__file__)

    moduledef.app_method("""
    def > other
        return (self <=> other) > 0
    end

    def < other
        return (self <=> other) < 0
    end

    def >= other
        return !((self <=> other) < 0)
    end

    def <= other
        return !((self <=> other) > 0)
    end

    def == other
        return (self <=> other) == 0
    end

    def between? min, max
        return self >= min && self <= max
    end
    """)
