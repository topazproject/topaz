class Range
  def each(&block)
    return self.enum_for unless block
    unless self.begin.respond_to?(:succ)
      raise TypeError.new("can't iterate from #{self.begin.class}")
    end

    case self.begin
    when String
      self.begin.upto(self.end, self.exclude_end?, &block)
    when Symbol
      self.begin.to_s.upto(self.end.to_s, self.exclude_end?) do |s|
        yield s.to_sym
      end
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

  def step(step_size = 1, &block)
    return self.to_enum(:step, step_size) unless block
    first = self.begin
    last = self.end

    if step_size.kind_of? Float or first.kind_of? Float or last.kind_of? Float
      # if any are floats they all must be
      begin
        step_size = Float(from = step_size)
        first     = Float(from = first)
        last      = Float(from = last)
      rescue ArgumentError
        raise TypeError, "no implicit conversion to float from #{from.class}"
      end
    else
      step_size = Topaz.convert_type(step_size, Integer, :to_int)
    end

    if step_size <= 0
      raise ArgumentError, "step can't be negative" if step_size < 0
      raise ArgumentError, "step can't be 0"
    end

    if first.kind_of?(Float)
      err = (first.abs + last.abs + (last - first).abs) / step_size.abs * Float::EPSILON
      err = 0.5 if err > 0.5
      if self.exclude_end?
        n = ((last - first) / step_size - err).floor
        n += 1 if n * step_size + first < last
      else
        n = ((last - first) / step_size + err).floor + 1
      end

      i = 0
      while i < n
        d = i * step_size + first
        d = last if last < d
        yield d
        i += 1
      end
    elsif first.kind_of?(Numeric)
      d = first
      while self.exclude_end? ? d < last : d <= last
        yield d
        d += step_size
      end
    else
      counter = 0
      each do |o|
        yield o if counter % step_size == 0
        counter += 1
      end
    end

    return self
  end

  def first(*args)
    if args.empty?
      self.begin
    else
      take(*args)
    end
  end

  def last(*args)
    args.empty? ? self.end : self.to_a.last(*args)
  end

  def min(&block)
    return super(&block) if block
    if (self.end < self.begin) || (self.exclude_end? && (self.end == self.begin))
      return nil
    end
    self.begin
  end

  def max(&block)
    return super(&block) if block || (self.exclude_end? && !self.end.kind_of?(Numeric))
    if (self.end < self.begin) || (self.exclude_end? && (self.end == self.begin))
      return nil
    end
    if self.exclude_end?
      unless self.end.kind_of?(Integer)
        raise TypeError.new("cannot exclude non Integer end value")
      end
      unless self.end.kind_of?(Integer)
        raise TypeError.new("cannot exclude end value with non Integer begin value")
      end
      self.end - 1
    else
      self.end
    end
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
  alias cover? include?
  alias member? include?

  def ==(other)
    return true if self.equal?(other)
    return false unless other.kind_of?(Range)

    return self.exclude_end? == other.exclude_end? &&
           self.first == other.first &&
           self.last == other.last
  end

  alias eql? ==

  def to_s
    "#{self.begin}#{self.exclude_end? ? '...' : '..'}#{self.end}"
  end
end
