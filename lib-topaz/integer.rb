class Integer < Numeric
  def downto(limit, &block)
    raise NotImplementedError, "Object#enum_for" if !block
    current = self
    while current >= limit
      yield current
      current -= 1
    end
  end
end
