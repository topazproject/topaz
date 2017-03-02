module Kernel
  def puts(*args)
    $stdout.puts(*args)
  end
  private :puts

  def gets(sep = $/, limit = nil)
    $stdin.gets(sep, limit)
  end
  private :gets

  def print(*args)
    $stdout.print(*args)
  end
  private :print

  def p(*args)
    args.each { |arg| $stdout.print(arg.inspect + "\n") }
  end
  private :p

  def <=>(other)
    self == other ? 0 : nil
  end

  def chop
    $_.chop!
  end
  private :chop

  def chomp
    $_.chomp!
  end
  private :chomp

  def Array(arg)
    if ary = Topaz.try_convert_type(arg, Array, :to_ary)
      ary
    elsif arg.respond_to?(:to_a) && ary = Topaz.try_convert_type(arg, Array, :to_a)
      ary
    else
      [arg]
    end
  end
  private :Array

  def String(arg)
    Topaz.convert_type(arg, String, :to_s)
  end
  module_function :String
  private :String

  def Integer(arg, base = nil)
    if arg.kind_of?(String)
      if arg.empty?
        raise ArgumentError.new("invalid value for Integer(): \"\"")
      else
        return arg.to_i(base || 0)
      end
    end

    raise ArgumentError.new("base specified for non string value") if base
    return Topaz.convert_type(arg, Fixnum, :to_int) if arg.nil?

    if arg.respond_to?(:to_int) && val = arg.to_int
      return val
    end
    Topaz.convert_type(arg, Fixnum, :to_i)
  end

  module_function :Integer
  private :Integer

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
  private :loop

  def `(cmd)
    cmd = Topaz.convert_type(cmd, String, :to_str)
    res = nil
    IO.popen(cmd) do |r|
      res = r.read
      Process.waitpid(r.pid)
    end
    res.to_s
  end
  private :`

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
  private :rand

  def caller(offset=0, limit=nil)
    begin
      raise "caller called"
    rescue Exception => e
      if limit
        return e.backtrace[(3 + offset), limit]
      else
        return e.backtrace[(3 + offset)..-1]
      end
    end
  end
  private :caller

  def require_relative(path)
    caller[0] =~ /^(.*):\d+:/
    caller_file = $1
    require File.join(File.dirname(File.expand_path(caller_file)), path)
  end

  def __dir__
    caller[0] =~ /^(.*):\d+:/
    caller_file = $1
    File.dirname(File.expand_path(caller_file))
  end
end
