class Numeric
  def eql?(other)
    self.class.equal?(other.class) && self == other
  end

  def to_int
    self.to_i
  end

  def abs
    self < 0 ? -self : self
  end
end
