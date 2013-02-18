class File < IO
  def self.open(filename, mode="r", perm=nil, opt=nil, &block)
    f = self.new filename, mode, perm, opt
    return f unless block
    begin
      return yield f
    ensure
      f.close
    end
  end

  def zero?
    self.size == 0
  end
end


class File::Stat
  def size?
    if self.size == 0
      nil
    else
      self.size
    end
  end

  def zero?
    self.size == 0
  end
end
