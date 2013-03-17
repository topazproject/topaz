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

