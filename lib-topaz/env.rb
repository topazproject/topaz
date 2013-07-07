class << ENV
  def to_hash
    {}.tap { |h| self.each { |k, v| h[k] = v } }
  end

  def empty?
    self.size == 0
  end

  def replace(hash)
    hash = Topaz.convert_type(hash, Hash, :to_hash)
    self.clear
    hash.each { |k, v| self[k] = v }
    self
  end

  def update(hash, &block)
    hash = Topaz.convert_type(hash, Hash, :to_hash)
    hash.each do |k, v|
      if block && self[k]
        self[k] = yield(k, self[k], v)
      else
        self[k] = v
      end
    end
    self
  end

  def clear
    self.each_key { |k| self[k] = nil }
  end

  def values
    self.map { |_, v| v }
  end

  def keys
    self.map { |k, _| k }
  end

  def value?(value)
    self.each_value { |v| return true if v == value }
    false
  end
  alias has_value? value?

  def key(value)
    self.each { |k, v| return k if v == value }
    nil
  end
  alias index key

  def each_value(&block)
    return enum_for(:each_value) unless block
    self.each { |_, v| yield(v) }
  end

  def each_key(&block)
    return enum_for(:each_key) unless block
    self.each { |k, _| yield(k) }
  end

  def assoc(key)
    key = Topaz.convert_type(key, String, :to_str)
    self.each { |k, v| return [k, v] if key == k }
    nil
  end

  def rassoc(value)
    value = Topaz.convert_type(value, String, :to_str)
    self.each { |k, v| return [k, v] if value == v }
    nil
  end

  def select!(&block)
    return enum_for(:select!) unless block
    modified = false
    self.each do |key, value|
      unless yield(key, value)
        delete(key)
        modified = true
      end
    end
    modified ? self : nil
  end

  def keep_if(&block)
    return enum_for(:keep_if) unless block
    select!(&block)
    self
  end

  def reject!(&block)
    return enum_for(:reject!) unless block
    modified = false
    self.each do |key, value|
      if yield(key, value)
        delete(key)
        modified = true
      end
    end
    modified ? self : nil
  end

  def delete_if(&block)
    return enum_for(:delete_if) unless block
    reject!(&block)
    self
  end

  def fetch(key, *args, &block)
    val = self[key]
    return val if val
    return yield(key) if block
    return args[0] if args.size == 1
    raise KeyError.new("key not found")
  end

  def to_s
    'ENV'
  end

  def inspect
    to_hash.inspect
  end

  def shift
    self.each do |k, v|
      delete(k)
      return [k, v]
    end
    nil
  end

  def values_at(*keys)
    keys.map { |k| self[k] }
  end

  def invert
    {}.tap { |h| self.each { |k, v| h[v] = k } }
  end

  def select(&block)
    return enum_for(:select) unless block
    to_hash.keep_if(&block)
  end

  def reject(&block)
    return enum_for(:reject) unless block
    to_hash.delete_if(&block)
  end

  def delete(key, &block)
    key = Topaz.convert_type(key, String, :to_str)
    if val = self[key]
      self[key] = nil
      return val
    end
    block ? yield(key) : nil
  end
end
