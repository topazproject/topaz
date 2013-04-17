class Topaz::Array
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

  def self.product(arrs, &block)
    n = arrs.size
    indices = [0] * n
    lens = arrs.map(&:size)
    pool = arrs.map(&:first)

    yield pool.dup

    while true do
      i = n - 1
      indices[i] += 1

      while indices[i] >= lens[i] do
        indices[i] = 0
        pool[i] = arrs[i][indices[i]]
        i -= 1
        return if i < 0
        indices[i] += 1
      end
      pool[i] = arrs[i][indices[i]]
      yield pool.dup
    end
  end
end
