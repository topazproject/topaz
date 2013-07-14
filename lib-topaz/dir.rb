class Dir
  def self.exists?(dirname)
    !!new(dirname)
  rescue Errno::ENOENT, Errno::ENOTDIR
    false
  end

  class << self
    alias :exist? :exists?
  end

  def self.open(path, opts = nil, &block)
    dir = new(path)
    if block
      value = nil

      begin
        value = yield dir
      ensure
        dir.close
      end

      value
    else
      dir
    end
  end

  def self.foreach(path, &block)
    return self.enum_for(:foreach, path) unless block

    open(path) do |dir|
      while s = dir.read
        yield s
      end
    end

    nil
  end
end
