module Comparable
  def >(other)
    return (self <=> other) > 0
  end

  def <(other)
    return (self <=> other) < 0
  end

  def >=(other)
    return !((self <=> other) < 0)
  end

  def <=(other)
    return !((self <=> other) > 0)
  end

  def ==(other)
    return (self <=> other) == 0
  end

  def between?(min, max)
    return self >= min && self <= max
  end
end
