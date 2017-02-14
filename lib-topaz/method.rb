class Method
  def to_proc
    Proc.new { |*args, &blk| self.call(*args, &blk) }
  end
end
