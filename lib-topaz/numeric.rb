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

  def div(other)
    raise ZeroDivisionError, "divided by 0" if other == 0
    (self / other).floor
  end

  def %(other)
    self - other * self.div(other)
  end
  alias modulo %

  def divmod(other)
    [div(other), self % other]
  end
end
