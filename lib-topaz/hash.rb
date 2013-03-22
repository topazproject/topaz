class Hash
  def each
    iter = Topaz::HashIterator.new(self)
    while true
      begin
        key, value = iter.next()
      rescue StopIteration
        return
      end
      yield key, value
    end
  end
  alias each_pair each

  def each_key
    each { |k, v| yield k }
  end

  def ==(other)
    if self.equal?(other)
      return true
    end
    if !other.kind_of?(Hash)
      return false
    end
    if self.size != other.size
      return false
    end
    self.each do |key, value|
      if !other.has_key?(key) || other[key] != value
        return false
      end
    end
    return true
  end

  def merge!(other, &block)
    other = other.to_hash unless other.kind_of? Hash
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

  def inspect
    result = "{"
    recursion = Thread.current.recursion_guard(:hash_inspect, self) do
      self.each_with_index do |key, i|
        if i > 0
          result << ", "
        end
        result << "#{key.inspect}=>#{self[key].inspect}"
      end
    end
    if recursion
      result << "..."
    end
    result << "}"
  end

  alias :to_s :inspect
end
