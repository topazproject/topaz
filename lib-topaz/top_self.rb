TOPLEVEL_BINDING = binding

class << self
  def include(*mods)
    Object.include(*mods)
  end

  def public(*attrs)
    Object.public(*attrs)
    return Object
  end

  def private(*attrs)
    Object.private(*attrs)
    return Object
  end

  def to_s
    "main"
  end

  alias inspect to_s
end
