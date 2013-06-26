class Regexp
  def to_regexp
    self
  end

  def hash
    to_s.hash
  end

  def ~
    self =~ $_
  end

  def self.try_convert(arg)
    Topaz.try_convert_type(arg, Regexp, :to_regexp)
  end
end
