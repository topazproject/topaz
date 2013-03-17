class Enumerator
  include Enumerable

  def initialize(obj = nil, method = :each, *args, &block)
    obj = Generator.new(&block) if obj.equal? nil
    
    @object = obj
    @method = method.to_sym
    @args = args
  end

  def each(&block)
    if block
      @object.send(@method, *@args, &block)
    else
      self
    end
  end

  def rewind
    @object.rewind if @object.respond_to?(:rewind)
    @nextvals = nil
    self
  end

  def peek
    if @nextvals.nil?
      @nextvals = []
      # naive implementation storing all values at once.
      # TODO: use Thread or Fiber once available
      if @nextvals.empty?
        @object.send(@method, *@args) do |*v|
          if v.size == 1 then
            @nextvals << v.first
          else
            @nextvals << v
          end
        end
      end
    end

    if @nextvals.empty?
      raise StopIteration.new("iteration reached an end")
    else
      return @nextvals.first
    end
  end

  def peek_values
    return Array(self.peek)
  end
  
  def next
    self.peek
    return @nextvals.shift 
  end

  def next_values
    return Array(self.next)
  end

  def with_object(obj, &block)
    return Enumerator.new(self, :with_object, obj) unless block
    self.each{ |*v| yield( *v, obj ) }
    return obj
  end

  class Generator
    def initialize(&block)
      @block = block
    end

    def each
      proc = Proc.new{ |*args| yield *args }
      @block.call Yielder.new(&proc)
    end
  end

  class Yielder
    def initialize(&block)
      @block = block
    end

    def yield(*args)
      @block.call *args
    end

    def <<(val)
      self.yield val
      self
    end
  end
end
