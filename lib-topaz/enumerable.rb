module Enumerable
  Undefined = Object.new

  def map
    result = []
    self.each do |x|
      result << (yield x)
    end
    result
  end

  alias collect map

  def inject(initial=Undefined, sym=Undefined, &block)
    if !block || !sym.equal?(Undefined)
      if sym.equal?(Undefined)
        sym = initial
        initial = Undefined
      end

      # Do the sym version

      sym = sym.to_sym

      each do |o|
        if initial.equal?(Undefined)
          initial = o
        else
          initial = initial.__send__(sym, o)
        end
      end

      # Block version
    else
      each do |o|
        if initial.equal?(Undefined)
          initial = o
        else
          initial = block.call(initial, o)
        end
      end
    end

    initial.equal?(Undefined) ? nil : initial
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
    ary = []
    self.each do |o|
      if block.call(o)
        ary << o
      end
    end
    ary
  end

  def include?(obj)
    self.each do |o|
      return true if o == obj
    end
    false
  end

  def drop n
    raise ArgumentError, 'attempt to drop negative size' if n < 0
    ary = self.to_a
    return [] if n > ary.size
    ary[n...ary.size]
  end

  def to_a
    result = []
    self.each do |i|
      result << i
    end
    result
  end

  def detect(ifnone = nil, &block)
    self.each do |o|
      return o if block.call(o)
    end
    return ifnone
  end
  alias find detect
end
