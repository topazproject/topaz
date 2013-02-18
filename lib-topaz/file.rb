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
end
