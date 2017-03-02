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

  def bytes(&block)
    return self.each_byte.to_a unless block
    each_byte(&block)
  end

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

  def rstrip
    duplicate = self.dup
    duplicate.rstrip!
    duplicate
  end

  def rstrip!
    self[/\s*$/] = ""
    self
  end

  def each_line(sep=$/)
    return to_enum(:each_line, sep) unless block_given?

    # weird edge case.
    if sep.nil?
      yield self
      return self
    end

    sep = sep.to_s

    pos = 0

    size = self.size
    orig_data = self.dup

    # If the separator is empty, we're actually in paragraph mode. This
    # is used so infrequently, we'll handle it completely separately from
    # normal line breaking.
    if sep.empty?
      sep = "\n\n"
      pat_size = 2

      while pos < size
        nxt = find_string(sep, pos)
        break unless nxt

        while self[nxt] == 10 and nxt < size
          nxt += 1
        end

        match_size = nxt - pos

        # string ends with \n's
        break if pos == size

        str = byteslice pos, match_size
        yield str unless str.empty?

        # detect mutation within the block
        if !self.equal?(orig_data) or self.size != size
          raise RuntimeError, "string modified while iterating"
        end

        pos = nxt
      end

      # No more separates, but we need to grab the last part still.
      fin = byteslice pos, self.size - pos
      yield fin if fin and !fin.empty?

    else

      # This is the normal case.
      pat_size = sep.size
      unmodified_self = clone

      while pos < size
        nxt = unmodified_self.find_string(sep, pos)
        break unless nxt

        match_size = nxt - pos
        str = unmodified_self.byteslice pos, match_size + pat_size
        yield str unless str.empty?

        pos = nxt + pat_size
      end

      # No more separates, but we need to grab the last part still.
      fin = unmodified_self.byteslice pos, self.size - pos
      yield fin unless fin.empty?
    end

    self
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

  def b
    self
  end
end
