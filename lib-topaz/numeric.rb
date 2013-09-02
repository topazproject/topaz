class Numeric
  def eql?(other)
    self.class.equal?(other.class) && self == other
  end

  def to_int
    self.to_i
  end

  def integer?
    false
  end

  def abs
    self < 0 ? -self : self
  end

  def abs2
    self * self
  end
  
  def %(other)
     self - other * self.div(other)
  end
  alias modulo %

  def div(other)
    raise ZeroDivisionError, "divided by 0" if other == 0
    (self / other).floor
  end

  def divmod(other)
    [div(other), self % other]
  end

  def zero?
    self == 0
  end

  def nonzero?
    self unless zero?
  end

  def +@
    self
  end

  def -@
    zero, value = self.coerce(0)
    zero - value
  end

  def truncate
    val = self.to_f
    if val > 0
      val.floor
    else
      val.ceil
    end
  end
end
