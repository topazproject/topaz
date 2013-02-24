class << self
  def include(*mods)
    Object.include(*mods)
  end

  def to_s
    return "main" if $0 == "-e"
    super
  end

  alias inspect to_s
end
