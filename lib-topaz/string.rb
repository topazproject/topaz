class String
  def eql?(other)
    if !other.kind_of?(String)
      false
    else
      self == other
    end
  end

  def swapcase
    copy = self.dup
    copy.swapcase!
    return copy
  end

  def upcase
    copy = self.dup
    copy.upcase!
    return copy
  end

  def downcase
    copy = self.dup
    copy.downcase!
    return copy
  end

  def capitalize
    copy = self.dup
    copy.capitalize!
    return copy
  end

  def empty?
    self.length == 0
  end

  def match(pattern)
    return Regexp.new(pattern).match(self)
  end

  def chomp(sep = $/)
    copy = self.dup
    copy.chomp!(sep)
    return copy
  end

  def chop
    copy = self.dup
    copy.chop!
    return copy
  end

  def reverse
    self.dup.reverse!
  end

  def succ
    self.dup.succ!
  end
  alias next succ
end
