module Enumerable
  def map
    result = []
    self.each do |x|
      result << (yield x)
    end
    result
  end

  alias collect map

  def first(n = nil)
    raise ArgumentError.new("negative array size") if n && n < 0
    count = n || 1
    result = []
    self.each do |elem|
      break if count.zero?
      result << elem
      count -= 1
    end
    n.nil? ? result[0] : result
  end

  def inject(memo)
    self.each do |x|
      memo = (yield memo, x)
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
    self.each do |o|
      return o if block.call(o)
    end
    return ifnone
  end
  alias find detect

  def take(n)
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
end
