class IO
  def << s
    write(s)
    return self
  end

  def each_line(sep=$/, limit=nil)
    if sep.is_a?(Fixnum) && limit.nil?
      limit = sep
      sep = $/
    end

    if sep.nil?
      yield(limit ? read(limit) : read)
      return self
    end

    if limit == 0
      raise ArgumentError.new("invalid limit: 0 for each_line")
    end

    rest = ""
    nxt = read(8192)
    need_read = false
    while nxt || rest
      if nxt and need_read
        rest = rest ? rest + nxt : nxt
        nxt = read(8192)
        need_read = false
      end

      line, rest = *rest.split(sep, 2)

      if limit && line.size > limit
        left = 0
        right = limit
        while right < line.size
          yield line[left...right]
          left, right = right, right + limit
        end
        rest = line[right - limit..-1] + sep + (rest || "")
      elsif rest || nxt.nil?
        yield line
      else
        need_read = true
      end
    end
    self
  end

  def readlines(sep=$/, limit=nil)
    lines = []
    each_line(sep, limit) { |line| lines << line }
    return lines
  end

  def self.readlines(name, *args)
    File.open(name) do |f|
      return f.readlines(*args)
    end
  end
end
