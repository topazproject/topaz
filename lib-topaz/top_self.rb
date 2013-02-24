class << self
  def include(*mods)
    Object.include(*mods)
  end

  def to_s
    "main"
  end

  alias inspect to_s
end
