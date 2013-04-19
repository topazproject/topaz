module Kernel
  def puts(*args)
    $stdout.puts(*args)
  end

  def gets(sep = $/, limit = nil)
    $stdin.gets(sep, limit)
  end

  def print(*args)
    $stdout.print(*args)
  end

  def p(*args)
    args.each { |arg| $stdout.print(arg.inspect + "\n") }
  end

  def <=>(other)
    self == other ? 0 : nil
  end

  def Array(arg)
    if arg.respond_to? :to_ary
      arg.to_ary
    elsif arg.respond_to? :to_a
      arg.to_a
    else
      [arg]
    end
  end

  def String(arg)
    arg.to_s
  end
  module_function :String

  def Integer(arg)
    arg.to_i
  end
  module_function :Integer

  def loop(&block)
    return enum_for(:loop) unless block
    begin
      while true
        yield
      end
    rescue StopIteration
      nil
    end
    nil
  end

  def `(cmd)
    cmd = cmd.to_str if cmd.respond_to?(:to_str)
    raise TypeError.new("can't convert #{cmd.class} into String") unless cmd.is_a?(String)
    res = ''
    IO.popen(cmd) do |r|
      res << r.read
      Process.waitpid(r.pid)
    end
    res
  end

  def to_enum(method = :each, *args)
    Enumerator.new(self, method, *args)
  end

  alias :enum_for :to_enum

  def rand(max = 1.0)
    if max.is_a?(Numeric)
      if max < 0
        return Random.rand(-max)
      elsif max.zero?
        return Random.rand
      elsif max.is_a?(Float) and max > 1
        return Random.rand(max).ceil
      end
    end
    Random.rand(max)
  end
end
