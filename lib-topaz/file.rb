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

  def self.truncate(filename, length)
    File.open(filename) do |f|
      f.truncate(length)
    end
  end

  def self.size(filename)
    return File.stat(filename).size
  end

  def self.zero?(filename)
    if filename.respond_to?(:to_path)
      filename = filename.to_path
    end

    begin
      File.size(filename) == 0
    rescue Errno::ENOENT
      false
    end
  end

  def size
    return self.stat.size
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
