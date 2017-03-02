class Fixnum < Integer
  def next
    succ
  end

  def succ
    self + 1
  end

  def upto(n, &block)
    return self.enum_for(:upto, n) if !block
    i = self
    while i <= n
      yield i
      i += 1
    end
    self
  end

  def even?
    self % 2 == 0
  end

  def odd?
    self % 2 != 0
  end

  def __id__
    self * 2 + 1
  end

  def magnitude
    abs
  end

  def step(limit, step=1, &block)
    return enum_for(:step, limit, step) unless block

    idx = self
    if limit.is_a?(Float) || step.is_a?(Float)
      idx = idx.to_f
    end
    while idx <= limit do
      yield idx
      idx += step
    end
  end
end
