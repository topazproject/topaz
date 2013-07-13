class Dir

  def self.exists?(dirname)
    if dirname.respond_to?(:to_path)
      dirname = dirname.to_path
    end
    begin
      !!new(dirname)
    rescue Errno::ENOENT, Errno::ENOTDIR
      false
    end
  end

  class << self
    alias :exist? :exists?
  end

end
