module Topaz
  class Array
    def self.flatten(array, out, level)
      modified = nil
      Thread.current.recursion_guard(:array_flatten, array) do
        array.each do |e|
          if level == 0
            out << e
          elsif e.respond_to?(:to_ary) && ary = ::Array.try_convert(e)
            modified = true
            flatten(ary, out, level - 1)
          else
            out << e
          end
        end
        return modified
      end
      raise ArgumentError, "tried to flatten recursive array"
    end
  end
end
