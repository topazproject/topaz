class Topaz::Array
  def self.flatten(array, out, level)
    modified = nil
    Thread.current.recursion_guard(:array_flatten, array) do
      array.each do |e|
        if level == 0
          out << e
        elsif ary = ::Array.try_convert(e)
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

    n = arrs.size
    indices = [0] * n

    yield pool[0, n]

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
      yield pool[0, n]
    end
  end

  def self.permutation(iterable, r, &block)
    n = iterable.size
    return if r > n || r < 0
    pool = iterable.dup
    cycles = (n - r + 1..n).to_a.reverse
    yield pool[0, r]

    while true
      stop = true
      i = r - 1
      while i >= 0
        cycles[i] -= 1
        if cycles[i] == 0
          e = pool[i]
          j = i + 1
          while j < n
            pool[j - 1] = pool[j]
            j += 1
          end
          pool[n - 1] = e
          cycles[i] = n - i
        else
          j = cycles[i]
          pool[i], pool[-j] = pool[-j], pool[i]
          yield pool[0, r]
          stop = false
          break
        end
        i -= 1
      end

      return if stop
    end
  end

  def self.combination(iterable, r, &block)
    n = iterable.size
    return if r > n || r < 0
    copy = iterable.dup
    pool = iterable.dup
    indices = (0...r).to_a
    yield pool[0, r]

    while true
      stop = true
      i = r - 1
      while i >= 0
        if indices[i] != i + n - r
          stop = false
          break
        end
        i -= 1
      end

      return if stop

      indices[i] += 1
      pool[i] = copy[indices[i]]
      j = i + 1
      while j < r
        indices[j] = indices[j - 1] + 1
        pool[j] = copy[indices[j]]
        j += 1
      end

      yield pool[0, r]
    end
  end

  def self.repeated_combination(iterable, r, &block)
    n = iterable.size
    return if r < 0 || (n < r && n == 0)
    copy = iterable.dup
    indices = [0] * r
    pool = indices.map { |i| copy[i] }

    yield pool[0, r]

    while true
      stop = true

      i = r - 1
      while i >= 0
        if indices[i] != n - 1
          stop = false
          break
        end
        i -= 1
      end
      return if stop

      ii = indices[i]
      j = i
      while j < r
        indices[j] = ii + 1
        pool[j] = copy[ii + 1]
        j += 1
      end
      yield pool[0, r]
    end
  end

  def self.repeated_permutation(iterable, r, &block)
    n = iterable.size
    return if r < 0 || (r != 0 && n == 0)
    if r == 0
      yield []
    else
      product([iterable.dup] * r, &block)
    end
  end
end
