class IO
  # Indexes for termios list.
  IFLAG = 0
  OFLAG = 1
  CFLAG = 2
  LFLAG = 3
  ISPEED = 4
  OSPEED = 5
  CC = 6
  include Topaz::TermIOConstants

  # def raw
  # end

  def raw!(&block)
    mode = Topaz.tcgetattr(fileno)
    mode[IFLAG] = mode[IFLAG] & ~(IGNBRK | BRKINT | PARMRK | ISTRIP | ICRNL |
                                  IXON)
    mode[OFLAG] = mode[OFLAG] & ~(OPOST)
    mode[CFLAG] = mode[CFLAG] & ~(CSIZE | PARENB)
    mode[CFLAG] = mode[CFLAG] | CS8
    mode[LFLAG] = mode[LFLAG] & ~(ECHO | ECHOE | ECHOK | ECHONL | ICANON | ISIG |
                                  IEXTEN)
    Topaz.tcsetattr(fileno, TCSANOW, mode)
    if block
      begin
        block[]
      ensure
        cooked!
      end
    end
  end

  # def cooked
  # end

  def cooked!
    mode = Topaz.tcgetattr(fileno)
    mode[IFLAG] = mode[IFLAG] | (BRKINT | ISTRIP | ICRNL | IXON)
    mode[OFLAG] = mode[OFLAG] | OPOST
    mode[LFLAG] = mode[LFLAG] | (ECHO | ECHOE | ECHOK | ECHONL | ICANON | ISIG |
                                 IEXTEN)
    Topaz.tcsetattr(fileno, TCSANOW, mode)
  end

  # def getch
  # end

  # def echo=
  # end

  # def echo
  # end

  # def echo?
  # end

  # def noecho
  # end

  # def winsize
  # end

  # def winsize=
  # end

  # def iflush
  # end

  # def oflush
  # end

  # def ioflush
  # end

  # def self.console
  # end

  # module Readable
  #   alias getch getc
  # end
end
