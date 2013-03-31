module Enumerable
  def first(*args)
    if args.empty?
      self.each { |e| return e }
      nil
    else
      take(*args)
    end
  end

  def map(&block)
    return self.enum_for(:map) unless block
    result = []
    self.each do |x|
      result << (yield x)
    end
    result
  end

  alias collect map

  def inject(*args)
    dropped = 0
    meth = nil
    case args.length
    when 0
      memo = self.first
      dropped = 1
    when 1
      memo = args[0]
    when 2
      memo = args[0]
      meth = args[1]
    end
    self.drop(dropped).each do |x|
      if meth
        memo = memo.send(meth, x)
      else
        memo = (yield memo, x)
      end
    end
    memo
  end

  alias reduce inject

  def each_with_index
    i = 0
    self.each do |obj|
      yield obj, i
      i += 1
    end
  end

  def all?(&block)
    self.each do |obj|
      return false unless (block ? block.call(obj) : obj)
    end
    true
  end

  def any?(&block)
    self.each do |obj|
      return true if (block ? block.call(obj) : obj)
    end
    false
  end

  def select(&block)
    return self.enum_for(:select) unless block
    result = []
    self.each do |o|
      if block.call(o)
        result << o
      end
    end
    result
  end

  def include?(obj)
    self.each do |o|
      return true if o == obj
    end
    false
  end
  alias member? include?

  def drop(n)
    raise ArgumentError.new("attempt to drop negative size") if n < 0
    result = self.to_a
    return [] if n > result.size
    result[n...result.size]
  end

  def drop_while(&block)
    result = []
    dropping = true
    self.each do |o|
      unless dropping && yield(o)
        result << o
        dropping = false
      end
    end
    result
  end

  def to_a
    result = []
    self.each do |i|
      result << i
    end
    result
  end
  alias entries to_a

  def detect(ifnone = nil, &block)
    return self.enum_for(:detect) unless block
    self.each do |o|
      return o if block.call(o)
    end
    return ifnone
  end
  alias find detect

  def take(n)
    n = Topaz.convert_type(n, Fixnum, :to_int)
    raise ArgumentError.new("attempt to take negative size") if n < 0
    result = []
    unless n == 0
      self.each do |o|
        result << o
        break if result.size == n
      end
    end
    result
  end

  def take_while(&block)
    result = []
    self.each do |o|
      break unless yield(o)
      result << o
    end
    result
  end

  def reject(&block)
    result = []
    self.each do |o|
      result << o unless yield(o)
    end
    result
  end

  def min
    inject do |minimum, current|
      if minimum > current
        current
      else
        minimum
      end
    end
  end

  def max
    inject do |maximum, current|
      if maximum < current
        current
      else
        maximum
      end
    end
  end

  def count(*args, &block)
    c = 0
    if args.empty?
      if block
        self.each { |e| c += 1 if block.call(e) }
      else
        self.each { c += 1 }
      end
    else
      arg = args[0]
      self.each { |e| c += 1 if e == arg }
    end
    c
  end
end
