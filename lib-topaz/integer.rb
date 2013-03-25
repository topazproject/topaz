class Integer < Numeric
  def downto(limit, &block)
    raise NotImplementedError.new("Object#enum_for") if !block
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
end
