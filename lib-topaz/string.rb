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

  def casecmp(other)
    other = Topaz.convert_type(other, String, :to_str)
    diff = self.length - other.length
    short = diff < 0
    long = diff > 0
    limit = (short ? self.length : other.length) - 1

    0.upto(limit) do |index|
      a, b = self[index], other[index]
      a.upcase!
      b.upcase!
      compared = a <=> b
      return compared unless compared == 0
    end

    short ? -1 : (long ? 1 : 0)
  end

  def empty?
    self.length == 0
  end

  def start_with?(*prefixes)
    prefixes.any? do |prefix|
      prefix = Topaz.try_convert_type(prefix, String, :to_str)
      next false unless prefix
      prelen = prefix.length
      next false if prelen > self.length
      0.upto(prelen - 1).all? { |index| self[index] == prefix[index] }
    end
  end

  def end_with?(*suffixes)
    suffixes.any? do |suffix|
      suffix = Topaz.try_convert_type(suffix, String, :to_str)
      next false unless suffix
      suflen = suffix.length
      next false if suflen > self.length
      (-suflen).upto(-1).all? { |index| self[index] == suffix[index] }
    end
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

  def each_char(&block)
    return self.enum_for(:each_char) unless block

    i = 0
    limit = self.length
    while i < limit
      yield self[i]
      i += 1
    end

    self
  end
  alias chars each_char

  def each_byte(&block)
    return self.enum_for(:each_byte) unless block

    i = 0
    limit = self.length
    while i < limit
      yield self.getbyte(i)
      i += 1
    end

    self
  end
  alias bytes each_byte

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

  def strip
    duplicate = self.dup
    duplicate.strip!
    duplicate
  end

  def chr
    self.dup[0] || self.dup
  end

  def replace(other)
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    other = Topaz.convert_type(other, String, :to_str)
    Topaz.infect(self, other)
    clear
    insert(0, other)
  end

  def self.try_convert(arg)
    Topaz.try_convert_type(arg, String, :to_str)
  end
end
