class File < IO
  def self.atime(filename)
    File.new(filename).atime
  end

  def self.ctime(filename)
    File.new(filename).ctime
  end

  def self.mtime(filename)
    File.new(filename).mtime
  end

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
    File.size(filename) == 0
  rescue Errno::ENOENT
    false
  end

  def size
    return self.stat.size
  end

  def zero?
    self.size == 0
  end

  class << self
    alias_method :realpath, :expand_path
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
