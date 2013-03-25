class Array
  def initialize(size_or_arr = nil, obj = nil, &block)
    self.clear
    if size_or_arr.nil?
      return self
    end
    if obj.nil?
      if size_or_arr.kind_of?(Array)
        return self.replace(size_or_arr)
      elsif size_or_arr.respond_to?(:to_ary)
        return self.replace(size_or_arr.to_ary)
      end
    end
    if !size_or_arr.respond_to?(:to_int)
      raise TypeError.new("can't convert #{size_or_arr.class} into Integer")
    end
    length = size_or_arr.to_int
    raise ArgumentError.new("negative array size") if length < 0
    if block
      # TODO: Emit "block supersedes default value argument" warning
      length.times { |i| self << yield(i) }
    else
      length.times { self << obj }
    end
    return self
  end

  def self.[](*args)
    args.inject(allocate) { |array, arg| array << arg}
  end

  def inspect
    result = "["
    recursion = Thread.current.recursion_guard(:array_inspect, self) do
      self.each_with_index do |obj, i|
        if i > 0
          result << ", "
        end
        result << obj.inspect
      end
    end
    if recursion
      result << "..."
    end
    result << "]"
  end

  alias :to_s :inspect

  def -(other)
    res = []
    self.each do |x|
      if !other.include?(x)
        res << x
      end
    end
    res
  end

  def at(idx)
    self[idx]
  end

  def each
    i = 0
    while i < self.length
      yield self[i]
      i += 1
    end
    return self
  end

  def zip(ary)
    result = []
    self.each_with_index do |obj, idx|
      result << [obj, ary[idx]]
    end
    result
  end

  def product(ary)
    result = []
    self.each do |obj|
      ary.each do |other|
        result << [obj, other]
      end
    end
    result
  end

  def compact
    self.select { |each| !each.nil? }
  end

  def compact!
    reject! { |obj| obj.nil? }
  end

  def reject!(&block)
    prev_size = self.size
    self.delete_if(&block)
    return nil if prev_size == self.size
    self
  end

  def assoc(key)
    detect { |arr| arr.is_a?(Array) && arr[0] == key }
  end

  def rassoc(value)
    detect { |arr| arr.is_a?(Array) && arr[1] == value }
  end

  def delete_if(&block)
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    return self.enum_for(:delete_if) unless block
    i = 0
    c = 0
    sz = self.size
    while i < sz - c
      item = self[i + c]
      if yield(item)
        c += 1
      else
        self[i] = item
        i += 1
      end
    end
    self.pop(c)
    self
  end

  def delete(obj, &block)
    sz = self.size
    self.delete_if { |o| o == obj }
    return obj if sz != self.size
    return yield if block
    return nil
  end

  def first(*args)
    if args.empty?
      self[0]
    else
      take(*args)
    end
  end

  def flatten(level = -1)
    list = []
    Thread.current.recursion_guard(:array_flatten, self) do
      self.each do |item|
        if level == 0
          list << item
        elsif ary = Array.try_convert(item)
          list.concat(ary.flatten(level - 1))
        else
          list << item
        end
      end
      return list
    end
    raise ArgumentError.new("tried to flatten recursive array")
  end

  def flatten!(level = -1)
    list = self.flatten(level)
    self.replace(list)
  end

  def sort(&block)
    dup.sort!(&block)
  end

  def ==(other)
    if self.equal?(other)
      return true
    end
    if !other.kind_of?(Array)
      if other.respond_to?(:to_ary)
        return other == self
      else
        return false
      end
    end
    if self.size != other.size
      return false
    end
    Thread.current.recursion_guard(:array_equals, self) do
      self.each_with_index do |x, i|
        if x != other[i]
          return false
        end
      end
    end
    return true
  end

  def eql?(other)
    if self.equal?(other)
      return true
    end
    if !other.kind_of?(Array)
      return false
    end
    if self.length != other.length
      return false
    end
    Thread.current.recursion_guard(:array_eqlp, self) do
      self.each_with_index do |x, i|
        if !x.eql?(other[i])
          return false
        end
      end
    end
    return true
  end

  def hash
    res = 0x345678
    self.each do |x|
      # We want to keep this within a fixnum range.
      res = Topaz.intmask((1000003 * res) ^ x.hash)
    end
    return res
  end

  def *(arg)
    return join(arg) if arg.respond_to? :to_str

    # MRI error cases
    argcls = arg.class
    begin
      arg = arg.to_int
    rescue Exception
      raise TypeError.new("can't convert #{argcls} into Fixnum")
    end
    raise TypeError.new("can't convert #{argcls} to Fixnum (argcls#to_int gives arg.class)") if arg.class != Fixnum
    raise ArgumentError.new("Count cannot be negative") if arg < 0

    return [] if arg == 0
    result = self.dup
    for i in 1...arg do
      result.concat(self)
    end
    result
  end

  def map!(&block)
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    self.each_with_index { |obj, idx| self[idx] = yield(obj) }
    self
  end

  def max(&block)
    max = self[0]
    self.each do |e|
      max = e if (block ? block.call(max, e) : max <=> e) < 0
    end
    max
  end

  def uniq!(&block)
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    seen = {}
    old_length = self.length
    i = 0
    shifted = 0
    while i < old_length do
      item = self[i]
      item = yield(item) if block
      if seen.include? item
        shifted += 1
      else
        seen[item] = nil
        self[i - shifted] = item if shifted > 0
      end
      i += 1
    end
    if shifted > 0
      self.slice!(-shifted, shifted)
      return self
    else
      return nil
    end
  end

  def uniq(&block)
    arr = self.dup
    arr.uniq!(&block)
    return arr
  end

  def values_at(*args)
    args.map { |n| self[n] }
  end

  def each_index(&block)
    0.upto(size - 1, &block)
    self
  end

  def reverse
    self.dup.reverse!
  end

  def reverse_each(&block)
    i = self.length - 1
    while i >= 0
      yield self[i]
      i -= 1
    end
    return self
  end
end
