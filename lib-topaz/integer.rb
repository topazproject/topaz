class Integer < Numeric
  def downto(limit, &block)
    return self.enum_for(:downto, limit) unless block
    current = self
    while current >= limit
      yield current
      current -= 1
    end
  end

  def times(&block)
    return self.enum_for(:times) unless block
    i = 0
    while i < self
      yield i
      i += 1
    end
    self
  end

  def to_i
    self
  end
  alias to_int to_i
  alias ceil to_i
  alias floor to_i
  alias truncate to_i
  alias ord to_i
  alias numerator to_i

  def denominator
    1
  end

  def integer?
    true
  end

  def next
    return self + 1
  end
  alias succ next

  def pred
    return self - 1
  end

  def even?
    (self % 2).zero?
  end

  def odd?
    !even?
  end
end
