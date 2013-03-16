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

  def loop
    while true
      yield
    end
    return nil
  end

  def `(cmd)
    cmd = cmd.to_str if cmd.respond_to?(:to_str)
    raise TypeError.new("can't convert #{cmd.class} into String") unless cmd.is_a?(String)
    IO.popen(cmd) { |r| r.read }
  end

  def rand(max = 0)
    random = Random.new.rand
    if max.is_a? Range
      (max.last - max.first) * random + max.first
    else
      max = max.to_int.abs
      if max.zero?
        random
      else
        (max * random).to_int
      end
    end
  end
end
