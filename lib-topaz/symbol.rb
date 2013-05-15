class Symbol
  def to_proc
    Proc.new do |*args|
      raise ArgumentError.new("no receiver given") if args.empty?
      args.shift.send(self, *args)
    end
  end

  def to_sym
    self
  end
  alias intern to_sym

  alias id2name to_s

  def succ
    self.to_s.succ.to_sym
  end
  alias next succ

  def capitalize
    self.to_s.capitalize.to_sym
  end

  def [](*args)
    self.to_s[*args]
  end
  alias slice []

  def swapcase
    self.to_s.swapcase.to_sym
  end
end
