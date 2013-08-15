module Process
  def self.wait
    waitpid
  end

  def self.waitpid2(pid = -1)
    pid = waitpid(pid)
    return [pid, $?]
  end

  def self.wait2(pid = -1)
    waitpid2(pid)
  end

  def self.waitall
    result = []
    result << wait2 while true
  rescue Errno::ECHILD
    result
  end

  class Status
    def initialize(pid, exitstatus)
      @pid = pid
      @exitstatus = exitstatus
    end

    def success?
      @exitstatus == 0
    end

    alias exited? success?

    def pid
      @pid
    end

    def exitstatus
      @exitstatus
    end

    alias to_i exitstatus
  end
end
