module Comparable
  def >(other)
    return Topaz.compare(self, other) > 0
  end

  def <(other)
    return Topaz.compare(self, other) < 0
  end

  def >=(other)
    return Topaz.compare(self, other) >= 0
  end

  def <=(other)
    return Topaz.compare(self, other) <= 0
  end

  def ==(other)
    begin
      compared = (self <=> other)
    rescue StandardError
      return false
    end

    return compared == 0
  end

  def between?(min, max)
    return self >= min && self <= max
  end
end
