class Enumerator
  include Enumerable

  def initialize(obj = nil, method = :each, *args, &block)
    obj = Generator.new(&block) if obj.nil?

    @object = obj
    @method = method.to_sym
    @args = args
    self
  end

  def each(&block)
    if block
      @object.send(@method, *@args, &block)
    else
      self
    end
  end

  def each_with_index(&block)
    return self.enum_for(:each_with_index) unless block

    i = 0
    self.each do |*e|
      v = (e.size == 1) ? e[0] : e
      val = yield(v, i)
      i += 1
      val
    end
  end

  def with_index(offset = nil, &block)
    return self.enum_for(:with_index, offset) unless block
    offset = offset ? Topaz.convert_type(offset, Fixnum, :to_int) : 0

    i = offset
    self.each do |*e|
      v = (e.size == 1) ? e[0] : e
      val = yield(v, i)
      i += 1
      val
    end
  end

  def rewind
    @object.rewind if @object.respond_to?(:rewind)
    @nextvals = nil
    @fiber = nil
    @finished = false
    self
  end

  def peek
    if @nextvals.nil?
      @nextvals = []
      @finished = false
      @fiber ||= Fiber.new do
        self.each do |*values|
          Fiber.yield(*values)
        end
        @finished = true
      end
    end

    if @nextvals.empty?
      @nextvals << @fiber.resume
      raise StopIteration.new("iteration reached an end") if @finished
    end

    return @nextvals.first
  end

  def peek_values
    return Array(self.peek)
  end

  def next
    raise StopIteration.new("iteration reached an end") if @finished
    self.peek
    return @nextvals.shift
  end

  def next_values
    return Array(self.next)
  end

  def with_object(obj, &block)
    return Enumerator.new(self, :with_object, obj) unless block
    self.each { |*v| yield(*v, obj) }
    return obj
  end

  class Generator
    include Enumerable

    def initialize(&block)
      @block = block
      self
    end

    def each
      proc = Proc.new { |*args| yield(*args) }
      @block.call(Yielder.new(&proc))
    end
  end

  class Yielder
    def initialize(&block)
      @block = block
      self
    end

    def yield(*args)
      @block.call(*args)
    end

    def <<(val)
      self.yield val
      self
    end
  end
end
