from rupypy.module import Module, ModuleDef


class Enumerable(Module):
    moduledef = ModuleDef("Enumerable", filepath=__file__)

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
    def all?(&block)
        self.each do |obj|
            return false unless (block ? block.call(obj) : obj)
        end
        true
    end
    """)

    moduledef.app_method("""
    def any?(&block)
        self.each do |obj|
            return true if (block ? block.call(obj) : obj)
        end
        false
    end
    """)

    moduledef.app_method("""
    def select(&block)
      ary = []
      self.each do |o|
        if block.call(o)
          ary << o
        end
      end
      ary
    end
    """)

    moduledef.app_method("""
    def include?(obj)
      self.each do |o|
        return true if o == obj
      end
      false
    end
    """)

    moduledef.app_method("""
    def drop n
        raise ArgumentError, 'attempt to drop negative size' if n < 0
        ary = self.to_a
        return [] if n > ary.size
        ary[n...ary.size]
    end
    """)

    moduledef.app_method("""
    def to_a
        result = []
        self.each do |i|
            result << i
        end
        result
    end
    """)

    moduledef.app_method("""
    def detect(ifnone = nil, &block)
        self.each do |o|
            return o if block.call(o)
        end
        return ifnone
    end
    alias find detect
    """)
