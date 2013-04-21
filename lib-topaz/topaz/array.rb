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

  def self.product(args, &block)
    arrs, pool, lens = [], [], []
    sumlen = 1
    args.each do |arr|
      arr = Topaz.convert_type(arr, Array, :to_ary)
      next unless arr
      size = arr.size
      return if size == 0
      sumlen *= size
      arrs << arr
      lens << size
      pool << arr[0]
    end
    raise RangeError.new("product result is too large") if sumlen > Topaz::FIXNUM_MAX

    yield pool.dup

    n = arrs.size
    indices = [0] * n

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
