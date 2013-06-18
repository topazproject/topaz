class Hash
  def each(&block)
    return self.enum_for(:each) if !block
    iter = Topaz::HashIterator.new(self)
    while true
      begin
        key, value = iter.next()
      rescue StopIteration
        return self
      end
      yield [key, value]
    end
  end
  alias each_pair each

  def self.[](*args)
    if args.size == 1
      arg = args[0]
      if hash = Hash.try_convert(arg)
        return allocate.replace(hash)
      elsif array = Array.try_convert(arg)
        h = new
        array.each do |a|
          next unless a = Array.try_convert(a)
          next if a.size < 1 || a.size > 2
          h[a[0]] = a[1]
        end
        return h
      end
    end

    return new if args.empty?
    raise ArgumentError.new("odd number of arguments for Hash") if args.size.odd?

    h = new
    i = 0
    while i < args.size
      h[args[i]] = args[i + 1]
      i += 2
    end
    h
  end

  def each_key(&block)
    return self.enum_for(:each_key) if !block
    each { |k, v| yield k }
  end

  def each_value(&block)
    return self.enum_for(:each_value) if !block
    each { |k, v| yield v }
  end

  def to_a
    res = []
    each do |k, v|
      res << [k, v]
    end
    res
  end

  def ==(other)
    return true if self.equal?(other)
    return false unless other.kind_of?(Hash)
    return false unless self.size == other.size
    Thread.current.recursion_guard(:hash_compare, self) do
      self.each do |key, value|
        return false unless other.has_key?(key) && value == other[key]
      end
    end
    true
  end

  def eql?(other)
    return true if self.equal?(other)
    return false unless other.kind_of?(Hash)
    return false unless self.size == other.size
    Thread.current.recursion_guard(:hash_eql, self) do
      self.each do |key, value|
        return false unless other.has_key?(key) && value.eql?(other[key])
      end
    end
    true
  end

  def merge!(other, &block)
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    other = Topaz.convert_type(other, Hash, :to_hash)
    if block
      other.each do |key, val|
        if has_key? key
          self[key] = block.call key, self[key], val
        else
          self[key] = val
        end
      end
    else
      other.each do |key, val|
        self[key] = val
      end
    end
    self
  end
  alias update merge!

  def merge(other, &block)
    dup.merge! other, &block
  end

  def assoc(key)
    each do |k, v|
      return [k, v] if key == k
    end
    nil
  end

  def rassoc(value)
    each do |k, v|
      return [k, v] if value == v
    end
    nil
  end

  def value?(value)
    each do |k, v|
      return true if value == v
    end
    false
  end
  alias has_value? value?

  def values_at(*keys)
    keys.map { |k| self[k] }
  end

  def key(value)
    each_pair do |k, v|
      return k if v == value
    end
    nil
  end
  # TODO: Emit "warning: Hash#index is deprecated; use Hash#key" warning
  alias index key

  def invert
    res = {}
    each do |k, v|
      res[v] = k
    end
    res
  end

  def inspect
    result = "{"
    recursion = Thread.current.recursion_guard(:hash_inspect, self) do
      self.each_with_index do |(key, value), i|
        if i > 0
          result << ", "
        end
        result << "#{key.inspect}=>#{value.inspect}"
      end
    end
    if recursion
      result << "..."
    end
    result << "}"
  end

  alias :to_s :inspect

  def select!(&block)
    return enum_for(:select!) unless block
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    modified = false
    each_pair do |key, value|
      unless yield key, value
        delete key
        modified = true
      end
    end
    modified ? self : nil
  end

  def keep_if(&block)
    return enum_for(:keep_if) unless block
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    select!(&block)
    self
  end

  def select(&block)
    return enum_for(:select) unless block
    dup.keep_if(&block)
  end

  def reject!(&block)
    return enum_for(:reject!) unless block
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    modified = false
    each_pair do |key, value|
      if yield key, value
        delete key
        modified = true
      end
    end
    modified ? self : nil
  end

  def delete_if(&block)
    return enum_for(:delete_if) unless block
    raise RuntimeError.new("can't modify frozen #{self.class}") if frozen?
    reject!(&block)
    self
  end

  def reject(&block)
    return enum_for(:reject) unless block
    dup.delete_if(&block)
  end

  def flatten(level = 1)
    level = Topaz.convert_type(level, Fixnum, :to_int)
    out = []
    Topaz::Array.flatten(self, out, level)
    out
  end

  def self.try_convert(arg)
    Topaz.try_convert_type(arg, Hash, :to_hash)
  end
end
