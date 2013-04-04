class Integer < Numeric
  def downto(limit, &block)
    return self.enum_for(:downto) unless block
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

  def ceil
    return self
  end

  def floor
    return self
  end

  def truncate
    return self
  end

  def denominator
    return 1
  end

  def numerator
    return self
  end

  def next
    return self + 1
  end
  alias succ next
end
