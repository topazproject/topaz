class Array
  def to_s
    result = "["
    each_with_index do |item, idx|
      result << ", " if idx > 0
      result << item.to_s
    end
    result << "]"
  end

  def -(other)
    result = []
    each do |item|
      result << item if !other.include?(item)
    end
    result
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
  end

  def zip(other)
    result = []
    each_with_index do |item, idx|
      result << [item, other[idx]]
    end
    result
  end

  def product(other)
    result = []
    each do |item1|
      other.each do |item2|
        result << [item1, item2]
      end
    end
    result
  end

  def compact
    select { |item| !item.nil? }
  end

  def compact!
    reject! { |item| item.nil? }
  end

  def reject!(&block)
    prev_size = self.size
    delete_if(&block)
    return nil if prev_size == size
    self
  end

  def assoc(key)
    detect { |item| item.is_a?(Array) && item[0] == key }
  end

  def rassoc(value)
    detect { |item| item.is_a?(Array) && item[1] == value }
  end

  def delete_if
    # TODO: Use check_frozen
    raise RuntimeError, "can't modify frozen #{self.class}" if frozen?

    # Current pointer where we're writing
    idx = 0
    # Number of elements we've skipped
    removed = 0
    # Store the size in a local variable
    size = self.size

    while idx + removed < size
      item = self[idx + removed]

      if yield(item)
        removed += 1
      else
        self[idx] = item
        idx += 1
      end
    end

    pop(removed)
    self
  end

  def delete(obj, &block)
    prev_size = self.size
    delete_if { |item| item == obj }
    return obj if prev_size != size
    return yield if block
    return nil
  end

  def first
    self[0]
  end

  def flatten(level = -1)
    result = []
    recursion = Thread.current.recursion_guard(self) do
      each do |obj|
        if level == 0
          result << item
        elsif ary = Array.try_convert(obj)
          result.concat(ary.flatten(level - 1))
        else
          result << item
        end
      end
    end

    raise ArgumentError, "tried to flatten recursive array" if recursion
    result
  end

  def flatten!(level = -1)
    result = flatten(level)
    clear
    concat(result)
  end

  def sort(&block)
    dup.sort!(&block)
  end

  def ==(other)
    return true  if equal?(other)
    return false if !other.kind_of?(Array)
    return false if size != other.size

    each_with_index do |item, idx|
      return false if item != other[idx]
    end

    return true
  end

  def eql?(other)
    return true if equal?(other)
    return false if !other.kind_of?(Array)
    return false if size != other.size

    each_with_index do |item, idx|
      return false if !item.eql?(other[idx])
    end

    return true
  end

  def hash
    result = 0x345678
    each do |item|
      # We want to keep this within a fixnum range.
      result = Topaz.intmask((1000003 * result) ^ item.hash)
    end
    result
  end

  def *(arg)
    return join(arg) if arg.respond_to?(:to_str)

    # TODO: Use Topaz::Type here
    # MRI error cases
    argcls = arg.class
    begin
      arg = arg.to_int
    rescue Exception
      raise TypeError, "can't convert #{argcls} into Fixnum"
    end
    raise TypeError, "can't convert #{argcls} to Fixnum (argcls#to_int gives arg.class)" if arg.class != Fixnum
    raise ArgumentError, "Count cannot be negative" if arg < 0

    return [] if arg == 0

    result = self.dup
    1.upto(arg) do
      result.concat(self)
    end
    result
  end

  # TODO: Refactor this into Enumerable
  def max(&block)
    max = self[0]
    each do |item|
      cmp = block ? yield(max, item) : max <=> item
      max = item if cmp < 0
    end
    max
  end

  def uniq!(&block)
    # TODO: Use check_frozen
    raise RuntimeError, "can't modify frozen #{self.class}" if frozen?
    prev_size = self.size
    seen = {}

    reject! do |item|
      item = yield(item) if block
      if seen.has_key?(item)
        true
      else
        seen[item] = true
        false
      end
    end
  end

  def uniq(&block)
    result = self.dup
    result.uniq!(&block)
    result
  end

  def values_at(*args)
    args.map { |idx| self[idx] }
  end
end
