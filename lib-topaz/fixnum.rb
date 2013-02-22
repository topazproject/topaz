class Fixnum < Integer
  def next
    succ
  end

  def succ
    self + 1
  end

  def times
    i = 0
    while i < self
      yield i
      i += 1
    end
  end

  def upto(n)
    i = self
    while i <= n
      yield i
      i += 1
    end
    self
  end

  def zero?
    self == 0
  end

  def nonzero?
    self != 0
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

  def step(limit, step=1)
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
