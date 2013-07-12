class Time
  def usec
    float = self.to_f
    (float - float.floor) * 1e6
  end

  def tv_usec
    self.usec.floor
  end

  def tv_sec
    self.to_f.floor
  end
end
