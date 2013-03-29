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

  def upto(max, exclusive = false, &block)
    return self.enum_for(:upto, max, exclusive) unless block

    maximum = Topaz.convert_type(max, String, :to_str)
    return self if self > maximum

    current = self.dup
    while current <= maximum
      break if current.length > maximum.length
      break if exclusive and current == maximum
      yield current
      # special handling to use ASCII map for single letters
      # ("9" followed by ":" not handled by String#succ)
      if current == "9" && self.length == 1 && maximum.length == 1 then
        current = ":"
      elsif current == "Z" && self.length == 1 && maximum.length == 1 then
        current = "["
      elsif current == "z" && self.length == 1 && maximum.length == 1 then
        current = "{"
      else
        current = current.succ
      end
    end

    return self
  end
end
