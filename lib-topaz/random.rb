class Random
  def bytes(n)
    n.times.map { rand(256).chr } .join
  end
end
