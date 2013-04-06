module Topaz
  class Array
    def self.flatten(array, level)
      list = array.class.allocate
      Thread.current.recursion_guard(:array_flatten, array) do
        array.each do |item|
          if level == 0
            list << item
          elsif ary = ::Array.try_convert(item)
            list.concat(flatten(ary, level - 1))
          else
            list << item
          end
        end
        return list
      end
      raise ArgumentError, "tried to flatten recursive array"
    end
  end
end
