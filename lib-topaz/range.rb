class Range
  def each(&block)
    raise NotImplementedError, "Object#enum_for" if !block

    if !(self.begin.respond_to? :succ)
      raise TypeError, "can't iterate from #{self.begin.class}"
    else
      i = self.begin
      if self.exclude_end?
        while (i <=> self.end) < 0 do
          yield i
          i = i.succ
        end
      else
        while (i <=> self.end) <= 0 do
          yield i
          i = i.succ
        end
      end
    end
    self
  end

  def ===(value)
    self.include?(value)
  end

  def include?(value)
    beg_compare = self.begin <=> value
    if !beg_compare
      return false
    end
    if beg_compare <= 0
      end_compare = value <=> self.end
      if self.exclude_end?
        return true if end_compare < 0
      else
        return true if end_compare <= 0
      end
    end
    return false
  end
end
