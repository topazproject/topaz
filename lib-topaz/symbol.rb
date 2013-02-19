class Symbol
  def to_proc
    Proc.new { |arg, *args| arg.send(self, *args) }
  end

  def to_sym
    self
  end

  def succ
    self.to_s.succ.to_sym
  end

  # `alias next succ` doesn't work due to this code being loaded
  # before W_SybolObject is added to the space
  def next
    succ
  end
end
