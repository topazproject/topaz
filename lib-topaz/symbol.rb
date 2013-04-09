class Symbol
  def to_proc
    Proc.new { |arg, *args| arg.send(self, *args) }
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

  def swapcase
    self.to_s.swapcase.to_sym
  end
end
