class Struct
  include Enumerable

  class << self
    alias subclass_new new
  end

  def self.new(klass_name, *attrs, &block)
    if klass_name
      begin
        klass_name = Topaz.convert_type(klass_name, String, :to_str)
      rescue TypeError
        attrs.unshift(klass_name)
        klass_name = nil
      end
    end

    attrs = attrs.map do |attr|
      case attr
      when String, Symbol
        Topaz.convert_type(attr, Symbol, :to_sym)
      else
        raise TypeError.new("#{attr.inspect} is not a symbol")
      end
    end

    klass = Class.new(self) do
      attr_accessor(*attrs)

      def self.new(*args, &block)
        return subclass_new(*args, &block)
      end

      def self.[](*args)
        return new(*args)
      end

      const_set(:STRUCT_ATTRS, attrs)
    end

    Struct.const_set(klass_name, klass) if klass_name
    klass.module_eval(&block) if block
    klass
  end

  def self.make_struct(name, attrs)
    new(name, *attrs)
  end

  def instance_variables
    # Hide the ivars used to store the struct fields
    attr_syms = self.class::STRUCT_ATTRS.map { |a| "@#{a}".to_sym }
    self.singleton_class.instance_variables - attr_syms
  end

  def initialize(*args)
    attrs = self.class::STRUCT_ATTRS

    unless args.length <= attrs.length
      raise ArgumentError.new("Expected #{attrs.size}, got #{args.size}")
    end

    attrs.each_with_index do |attr, i|
      instance_variable_set(:"@#{attr}", args[i])
    end
  end

  private :initialize

  def ==(other)
    return false if self.class != other.class

    Thread.current.recursion_guard(:==, self) do
      return self.values == other.values
    end
    true
  end

  def eql?(other)
    return true if equal?(other)
    return false if self.class != other.class

    Thread.current.recursion_guard(:eql?, self) do
      self.class::STRUCT_ATTRS.each do |var|
        mine = instance_variable_get(:"@#{var}")
        theirs = other.instance_variable_get(:"@#{var}")
        return false unless mine.eql?(theirs)
      end
    end
    true
  end

  def [](var)
    case var
    when Symbol, String
      unless self.class::STRUCT_ATTRS.include?(var.to_sym)
        raise NameError.new("no member '#{var}' in struct")
      end
    else
      var = Topaz.convert_type(var, Fixnum, :to_int)
      a_len = self.class::STRUCT_ATTRS.length
      if var > a_len - 1
        raise IndexError.new("offset #{var} too large for struct(size:#{a_len})")
      end
      if var < -a_len
        raise IndexError.new("offset #{var + a_len} too small for struct(size:#{a_len})")
      end
      var = self.class::STRUCT_ATTRS[var]
    end

    instance_variable_get(:"@#{var}")
  end

  def []=(var, obj)
    case var
    when Symbol, String
      unless self.class::STRUCT_ATTRS.include?(var.to_sym)
        raise NameError, "no member '#{var}' in struct"
      end
    else
      var = Topaz.convert_type(var, Fixnum, :to_int)
      a_len = self.class::STRUCT_ATTRS.length
      if var > a_len - 1
        raise IndexError, "offset #{var} too large for struct(size:#{a_len})"
      end
      if var < -a_len
        raise IndexError, "offset #{var + a_len} too small for struct(size:#{a_len})"
      end
      var = self.class::STRUCT_ATTRS[var]
    end

    instance_variable_set(:"@#{var}", obj)
  end

  def each(&block)
    return to_enum(:each) unless block
    values.each(&block)
    self
  end

  def each_pair(&block)
    return to_enum(:each_pair) unless block
    self.class::STRUCT_ATTRS.each do |var|
      yield var, instance_variable_get(:"@#{var}")
    end
    self
  end

  def hash
    hash_val = size

    recursion = Thread.current.recursion_guard(:hash, self) do
      self.class::STRUCT_ATTRS.each do |var|
        hash_val ^= instance_variable_get(:"@#{var}").hash
      end
    end

    hash_val
  end

  def length
    self.class::STRUCT_ATTRS.length
  end
  alias size length

  def self.length
    self::STRUCT_ATTRS.size
  end

  class << self
    alias size length
  end

  def self.members
    self::STRUCT_ATTRS.dup
  end

  def members
    self.class.members
  end

  def select(&block)
    to_a.select(&block)
  end

  def to_a
    self.class::STRUCT_ATTRS.map { |var| instance_variable_get :"@#{var}" }
  end
  alias values to_a

  def values_at(*args)
    to_a.values_at(*args)
  end

  def to_s
    recursion = Thread.current.recursion_guard(:to_s, self) do
      values = []

      self.class::STRUCT_ATTRS.each do |var|
        val = instance_variable_get :"@#{var}"
        values << "#{var}=#{val.inspect}"
      end

      name = self.class.name

      if name.nil? || name.empty?
        return "#<struct #{values.join(', ')}>"
      else
        return "#<struct #{self.class.name} #{values.join(', ')}>"
      end
    end
    return "[...]" if recursion
  end
  alias inspect to_s

  Struct.new('Tms', :utime, :stime, :cutime, :cstime, :tutime, :tstime) do
    def initialize(utime=nil, stime=nil, cutime=nil, cstime=nil,
                   tutime=nil, tstime=nil)
      @utime = utime
      @stime = stime
      @cutime = cutime
      @cstime = cstime
      @tutime = tutime
      @tstime = tstime
    end
  end
end
