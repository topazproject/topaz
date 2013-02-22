module Process
  def self.wait
    waitpid
  end

  def self.waitpid2(pid = -1)
    pid = waitpid(pid)
    return [pid, $?]
  end

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
