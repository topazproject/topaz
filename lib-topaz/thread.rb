class Thread
  class << self
    attr_writer :abort_on_exception

    def abort_on_exception
      @abort_on_exception ||= false
    end
  end

  attr_writer :abort_on_exception

  def abort_on_exception
    @abort_on_exception ||= (Thread.abort_on_exception || false)
  end
end
