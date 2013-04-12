class Thread
  class << self
    def abort_on_exception=(value)
      @abort_on_exception = !!value
    end

    def abort_on_exception
      @abort_on_exception ||= false
    end
  end

  def abort_on_exception=(value)
    @abort_on_exception = !!value
  end

  def abort_on_exception
    @abort_on_exception ||= (Thread.abort_on_exception || false)
  end
end
