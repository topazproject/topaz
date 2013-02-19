module Process
  class Status
    def initialize(pid, exitstatus)
      @pid = pid
      @exitstatus = exitstatus
    end

    def pid
      @pid
    end

    def exitstatus
      @exitstatus
    end

    alias to_i exitstatus
  end
end
