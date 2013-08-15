class Time
  def usec
    (self.to_f * 1e6 % 1e6).floor
  end

  def tv_usec
    self.usec.floor
  end

  def tv_sec
    self.to_f.floor
  end

  def succ
    Time.at(self.to_i + 1)
  end

  def <=>(other)
    if other.kind_of?(Time)
      self.to_f <=> other.to_f
    else
      compare = (other <=> self)
      if compare.nil?
        nil
      elsif compare > 0
        -1
      elsif compare < 0
        1
      else
        0
      end
    end
  end

end
