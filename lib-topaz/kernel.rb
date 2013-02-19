module Kernel
  def puts *args
    $stdout.puts(*args)
  end

  def print *args
    $stdout.print(*args)
  end

  def p *args
    args.each { |arg| $stdout.print(arg.inspect + "\n") }
  end

  alias fail raise

  def Array arg
    if arg.respond_to? :to_ary
      arg.to_ary
    elsif arg.respond_to? :to_a
      arg.to_a
    else
      [arg]
    end
  end

  def String arg
    arg.to_s
  end
  module_function :String

  def Integer arg
    arg.to_i
  end
  module_function :Integer

  def loop
    while true
      yield
    end
    return nil
  end
end
