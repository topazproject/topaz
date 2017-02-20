class Array
  def initialize(size_or_arr = nil, obj = nil, &block)
    self.clear
    return self if size_or_arr.nil?
    if obj.nil?
      if ary = Topaz.try_convert_type(size_or_arr, Array, :to_ary)
        return self.replace(ary)
      end
    end
    length = Topaz.convert_type(size_or_arr, Fixnum, :to_int)
    raise ArgumentError.new("negative array size") if length < 0
    if block
      # TODO: Emit "block supersedes default value argument" warning
      length.times { |i| self << yield(i) }
    else
      self.concat([obj] * length)
    end
    return self
  end

  def self.[](*args)
    allocate.concat(args)
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

  def at(idx)
    self[idx]
  end

  def fetch(*args, &block)
    i = Topaz.convert_type(args[0], Fixnum, :to_int)
    if i < -self.length || i >= self.length
      return block.call(args[0]) if block
      return args[1] if args.size > 1
      raise IndexError.new("index #{i} outside of array bounds: -#{self.length}...#{self.length}")
    else
      self[i]
    end
  end

  def each(&block)
    return self.enum_for(:each) unless block
    i = 0
    while i < self.length
      yield self[i]
      i += 1
    end
    return self
  end

  def product(*args, &block)
    args = args.unshift(self)
    if block
      Topaz::Array.product(args, &block)
      self
    else
      out = self.class.allocate
      Topaz::Array.product(args) { |e| out << e }
      out
    end
  end

  def compact
    self.select { |each| !each.nil? }
  end

  def compact!
    reject! { |obj| obj.nil? }
  end

  def select!(&block)
    return self.enum_for(:select!) unless block
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    new_arr = self.select(&block)
    if new_arr.size != self.size
      self.replace(new_arr)
      self
    end
  end

  def keep_if(&block)
    self.select!(&block) || self
  end

  def reject!(&block)
    return self.enum_for(:reject!) unless block
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
    return self.enum_for(:delete_if) unless block
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
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
    last_matched_element = nil
    self.delete_if do |o|
      if match = (o == obj)
        last_matched_element = o
      end
      match
    end
    return last_matched_element if sz != self.size
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
    level = Topaz.convert_type(level, Fixnum, :to_int)
    out = self.class.allocate
    Topaz::Array.flatten(self, out, level)
    out
  end

  def flatten!(level = -1)
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    level = Topaz.convert_type(level, Fixnum, :to_int)
    out = self.class.allocate
    if Topaz::Array.flatten(self, out, level)
      self.replace(out)
    end
  end

  def sort(&block)
    Array.new(self).sort!(&block)
  end

  def sort_by(&block)
    Array.new(self).sort_by!(&block)
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

  def <=>(other)
    return 0 if self.equal?(other)
    other = Array.try_convert(other)
    return nil unless other
    cmp_len = (self.size <=> other.size)
    return cmp_len if cmp_len != 0
    Thread.current.recursion_guard(:array_comparison, self) do
      self.each_with_index do |e, i|
        cmp = (e <=> other[i])
        return cmp if cmp != 0
      end
      return 0
    end
    nil
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
    Thread.current.recursion_guard(:array_hash, self) do
      self.each do |x|
        # We want to keep this within a fixnum range.
        res = Topaz.intmask((1000003 * res) ^ x.hash)
      end
    end
    return res
  end

  def map!(&block)
    return self.enum_for(:map!) unless block
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    self.each_with_index { |obj, idx| self[idx] = yield(obj) }
    self
  end

  alias :collect! :map!

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
    out = []
    args.each do |arg|
      if arg.is_a?(Range)
        v = self[arg]
        out.concat(v) if v
      else
        out << self[arg]
      end
    end
    out
  end

  def each_index(&block)
    return self.enum_for(:each_index) unless block
    0.upto(size - 1, &block)
    self
  end

  def reverse
    Array.new(self).reverse!
  end

  def reverse_each(&block)
    return self.enum_for(:reverse_each) unless block
    i = self.length - 1
    while i >= 0
      yield self[i]
      i -= 1
    end
    return self
  end

  def index(obj = nil, &block)
    return self.enum_for(:index) if !obj && !block
    each_with_index do |e, i|
      return i if obj ? (e == obj) : block.call(e)
    end
    nil
  end

  alias :find_index :index

  def rindex(obj = nil, &block)
    return self.enum_for(:rindex) if !obj && !block
    i = size - 1
    while i >= 0
      e = self[i]
      return i if obj ? (e == obj) : block.call(e)
      i = size if i > size
      i -= 1
    end
    nil
  end

  def rotate(n = 1)
    Array.new(self).rotate!(n)
  end

  def count(*args, &block)
    c = 0
    if args.empty?
      if block
        self.each { |e| c += 1 if block.call(e) }
      else
        c = self.length
      end
    else
      arg = args[0]
      self.each { |e| c += 1 if e == arg }
    end
    c
  end

  def shuffle!
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    (self.length - 1).downto(1) do |idx|
      other = rand(idx + 1)
      self[other], self[idx] = self[idx], self[other]
    end
    self
  end

  def shuffle
    arr = Array.new(self)
    arr.shuffle!
    arr
  end

  def to_a
    self.instance_of?(Array) ? self : Array.new(self)
  end

  def &(other)
    other = Topaz.convert_type(other, Array, :to_ary)
    h = {}
    other.each { |e| h[e] = true }
    self.select { |e| h.delete(e) }
  end

  def |(other)
    other = Topaz.convert_type(other, Array, :to_ary)
    h = {}
    self.each { |e| h[e] = true }
    other.each { |e| h.fetch(e) { |v| h[v] = true } }
    h.keys
  end

  def -(other)
    other = Topaz.convert_type(other, Array, :to_ary)
    h = {}
    other.each { |e| h[e] = true }
    self.reject { |e| h.has_key?(e) }
  end

  def permutation(r = nil, &block)
    return self.enum_for(:permutation, r) unless block
    r = r ? Topaz.convert_type(r, Fixnum, :to_int) : self.size
    Topaz::Array.permutation(self, r, &block)
    self
  end

  def combination(r = nil, &block)
    return self.enum_for(:combination, r) unless block
    r = r ? Topaz.convert_type(r, Fixnum, :to_int) : self.size
    Topaz::Array.combination(self, r, &block)
    self
  end

  def repeated_combination(r, &block)
    return self.enum_for(:repeated_combination, r) unless block
    r = Topaz.convert_type(r, Fixnum, :to_int)
    Topaz::Array.repeated_combination(self, r, &block)
    self
  end

  def repeated_permutation(r, &block)
    return self.enum_for(:repeated_permutation, r) unless block
    r = Topaz.convert_type(r, Fixnum, :to_int)
    Topaz::Array.repeated_permutation(self, r, &block)
    self
  end

  def fill(*args, &block)
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?

    if block
      raise ArgumentError.new("wrong number of arguments (#{args.size} for 0..2)") if args.size > 2
      one, two = args
    else
      raise ArgumentError.new("wrong number of arguments (#{args.size} for 1..3)") if args.empty? || args.size > 3
      obj, one, two = args
    end

    if one.kind_of?(Range)
      raise TypeError.new("no implicit conversion of Range into Integer") if two

      left = Topaz.convert_type(one.begin, Fixnum, :to_int)
      left += size if left < 0
      raise RangeError.new("#{one} out of range") if left < 0

      right = Topaz.convert_type(one.end, Fixnum, :to_int)
      right += size if right < 0
      right += 1 unless one.exclude_end?
      return self if right <= left

    elsif one
      left = Topaz.convert_type(one, Fixnum, :to_int)
      left += size if left < 0
      left = 0 if left < 0

      if two
        right = Topaz.convert_type(two, Fixnum, :to_int)
        return self if right == 0
        right += left
      else
        right = size
      end
    else
      left = 0
      right = size
    end

    right_bound = (right > size) ? size : right

    i = left
    while i < right_bound
      self[i] = block ? yield(i) : obj
      i += 1
    end

    if left > size
      self.concat([nil] * (left - size))
      i = size
    end

    while i < right
      self << (block ? yield(i) : obj)
      i += 1
    end

    self
  end

  def transpose
    return [] if self.empty?

    max = nil
    lists = self.map do |ary|
      ary = Topaz.convert_type(ary, Array, :to_ary)
      max ||= ary.size
      raise IndexError.new("element size differs (#{ary.size} should be #{max})") if ary.size != max
      ary
    end

    out = []
    max.times do |i|
      out << lists.map { |l| l[i] }
    end
    out
  end

  def sample(*args)
    case args.size
    when 0
      return self[Kernel.rand(size)]
    when 1
      arg = args[0]
      if o = Topaz.try_convert_type(arg, Hash, :to_hash)
        options = o
        count = nil
      else
        options = nil
        count = Topaz.convert_type(arg, Fixnum, :to_int)
      end
    when 2
      count = Topaz.convert_type(args[0], Fixnum, :to_int)
      options = Topaz.convert_type(args[1], Hash, :to_hash)
    else
      raise ArgumentError.new("wrong number of arguments (#{args.size} for 1)")
    end

    raise ArgumentError.new("negative sample number") if count and count < 0

    rng = options[:random] if options
    rng = Kernel unless rng && rng.respond_to?(:rand)

    unless count
      random = Topaz.convert_type(rng.rand, Float, :to_f)
      raise RangeError.new("random number too big #{random}") if random < 0 || random >= 1.0

      return self[random * size]
    end

    count = size if count > size
    out = Array.new(self)

    count.times do |i|
      random = Topaz.convert_type(rng.rand, Float, :to_f)
      raise RangeError.new("random number too big #{random}") if random < 0 || random >= 1.0

      r = (random * size).to_i
      out[i], out[r] = out[r], out[i]
    end

    return (count == size) ? out : out[0, count]
  end

  def self.try_convert(arg)
    Topaz.try_convert_type(arg, Array, :to_ary)
  end
end
