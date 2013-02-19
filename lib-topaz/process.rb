module Process
  class Status
    def initialize(pid, exitstatus)
      @pid = pid
      @exitstatus = exitstatus
    end

    attr_reader :pid, :exitstatus

    alias to_i exitstatus
  end
end
