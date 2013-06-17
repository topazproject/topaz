module Enumerable
  def first(*args)
    if args.empty?
      self.each_entry { |e| return e }
      nil
    else
      take(*args)
    end
  end

  def map(&block)
    return self.enum_for(:map) unless block
    result = []
    self.each do |*x|
      result << yield(*x)
    end
    result
  end

  alias collect map

  def inject(*args, &block)
    op = nil
    dropped = 0
    memo = nil
    case args.size
    when 0
      dropped = 1
    when 1
      if args[0].is_a?(Symbol)
        dropped = 1
        op = args[0]
      else
        memo = args[0]
      end
    when 2
      memo = args[0]
      op = args[1]
    end
    self.each_with_index do |e, i|
      if i < dropped
        memo = e
      else
        memo = op ? memo.send(op, e) : yield(memo, e)
      end
    end
    memo
  end
  alias reduce inject

  def each_with_index(*args, &block)
    return self.enum_for(:each_with_index, *args) if !block
    i = 0
    self.each_entry(*args) do |obj|
      yield obj, i
      i += 1
    end
  end

  def each_with_object(memo, &block)
    return self.enum_for(:each_with_object, memo) unless block
    self.each_entry do |elm|
      yield elm, memo
    end
    memo
  end

  def each_entry(*args, &block)
    return self.enum_for(:each_entry, *args) unless block
    each(*args) do |*e|
      v = (e.size == 1) ? e[0] : e
      yield v
    end
    self
  end

  def reverse_each(&block)
    return self.enum_for(:reverse_each) unless block
    self.to_a.reverse_each(&block)
    self
  end

  def all?(&block)
    if block
      self.each { |*e| return false unless yield(*e) }
    else
      self.each_entry { |e| return false unless e }
    end
    true
  end

  def any?(&block)
    if block
      self.each { |*e| return true if yield(*e) }
    else
      self.each_entry { |e| return true if e }
    end
    false
  end

  def select(&block)
    return self.enum_for(:select) unless block
    result = []
    self.each_entry do |o|
      if block.call(o)
        result << o
      end
    end
    result
  end

  alias :find_all :select

  def include?(obj)
    self.each_entry do |o|
      return true if o == obj
    end
    false
  end
  alias member? include?

  def drop(n)
    n = Topaz.convert_type(n, Fixnum, :to_int)
    raise ArgumentError.new("attempt to drop negative size") if n < 0
    result = self.to_a
    return [] if n > result.size
    result[n...result.size]
  end

  def drop_while(&block)
    return self.enum_for(:drop_while) if !block
    result = []
    dropping = true
    self.each_entry do |o|
      unless dropping && yield(o)
        result << o
        dropping = false
      end
    end
    result
  end

  def to_a(*args)
    result = []
    self.each_entry(*args) do |i|
      result << i
    end
    result
  end
  alias entries to_a

  def detect(ifnone = nil, &block)
    return self.enum_for(:detect, ifnone) unless block
    self.each_entry do |o|
      return o if block.call(o)
    end
    ifnone.is_a?(Proc) ? ifnone.call : ifnone
  end
  alias find detect

  def take(n)
    n = Topaz.convert_type(n, Fixnum, :to_int)
    raise ArgumentError.new("attempt to take negative size") if n < 0
    result = []
    unless n == 0
      self.each_entry do |o|
        result << o
        break if result.size == n
      end
    end
    result
  end

  def take_while(&block)
    return self.enum_for(:take_while) unless block
    result = []
    self.each_entry do |o|
      break unless yield(o)
      result << o
    end
    result
  end

  def reject(&block)
    return self.enum_for(:reject) unless block
    result = []
    self.each_entry do |o|
      result << o unless yield(o)
    end
    result
  end

  def max(&block)
    max = nil
    self.each_with_index do |e, i|
      max = e if i == 0 || Topaz.compare(e, max, &block) > 0
    end
    max
  end

  def min(&block)
    min = nil
    self.each_with_index do |e, i|
      min = e if i == 0 || Topaz.compare(e, min, &block) < 0
    end
    min
  end

  def max_by(&block)
    return self.enum_for(:max_by) unless block
    max = maxv = nil
    self.each_with_index do |e, i|
      ev = yield(e)
      max, maxv = e, ev if i == 0 || Topaz.compare(ev, maxv) > 0
    end
    max
  end

  def min_by(&block)
    return self.enum_for(:min_by) unless block
    min = minv = nil
    self.each_with_index do |e, i|
      ev = yield(e)
      min, minv = e, ev if i == 0 || Topaz.compare(ev, minv) < 0
    end
    min
  end

  def minmax(&block)
    min = max = nil
    self.each_with_index do |e, i|
      min = e if i == 0 || Topaz.compare(e, min, &block) < 0
      max = e if i == 0 || Topaz.compare(e, max, &block) > 0
    end
    [min, max]
  end

  def minmax_by(&block)
    return self.enum_for(:minmax_by) unless block
    min = max = minv = maxv = nil
    self.each_with_index do |e, i|
      ev = yield(e)
      max, maxv = e, ev if i == 0 || Topaz.compare(ev, maxv) > 0
      min, minv = e, ev if i == 0 || Topaz.compare(ev, minv) < 0
    end
    [min, max]
  end

  def partition(&block)
    return self.enum_for(:partition) unless block
    a, b = [], []
    self.each_entry do |e|
      block.call(e) ? a.push(e) : b.push(e)
    end
    [a, b]
  end

  def count(*args, &block)
    c = 0
    if args.empty?
      if block
        self.each { |e| c += 1 if block.call(e) }
      else
        self.each { c += 1 }
      end
    else
      arg = args[0]
      self.each { |e| c += 1 if e == arg }
    end
    c
  end

  def one?(&block)
    c = 0
    if block
      self.each do |*e|
        c += 1 if yield(*e)
        return false if c > 1
      end
    else
      self.each_entry do |e|
        c += 1 if e
        return false if c > 1
      end
    end
    c == 1
  end

  def none?(&block)
    if block
      self.each { |*e| return false if yield(*e) }
    else
      self.each_entry { |e| return false if e }
    end
    true
  end

  def group_by(&block)
    return self.enum_for(:group_by) unless block
    h = {}
    self.each_entry do |e|
      v = yield e
      a = h.fetch(v) { |v| h[v] = [] }
      a << e
    end
    h
  end

  def find_index(obj = nil, &block)
    return self.enum_for(:find_index) if !obj && !block
    i = 0
    each do |e|
      return i if obj ? (e == obj) : block.call(e)
      i += 1
    end
    nil
  end

  def each_cons(num, &block)
    return self.enum_for(:each_cons, num) if !block
    num = Topaz.convert_type(num, Fixnum, :to_int)
    raise ArgumentError.new("invalid size") if num <= 0
    buf = []
    self.each_with_index do |e, i|
      buf << e
      if i == num - 1
        yield buf.dup
      elsif i >= num
        buf.shift
        yield buf.dup
      end
    end
    nil
  end

  def each_slice(num, &block)
    return self.enum_for(:each_slice, num) if !block
    num = Topaz.convert_type(num, Fixnum, :to_int)
    raise ArgumentError.new("invalid slice size") if num <= 0
    buf = []
    self.each_entry do |e|
      buf << e
      if buf.size == num
        yield buf
        buf = []
      end
    end
    yield buf unless buf.empty?
    nil
  end

  def sort(&block)
    to_a.sort!(&block)
  end

  def sort_by(&block)
    to_a.sort_by!(&block)
  end

  def collect_concat(&block)
    return self.enum_for(:collect_concat) unless block
    out = []
    self.each do |e|
      v = yield(e)
      if ary = Array.try_convert(v)
        out.concat(ary)
      else
        out << v
      end
    end
    out
  end
  alias flat_map collect_concat

  def zip(*lists, &block)
    lists = lists.map do |l|
      l.respond_to?(:to_ary) ? l.to_ary : l.to_enum(:each)
    end

    index = -1
    tail = proc do
      index += 1
      lists.map do |l|
        l.kind_of?(Array) ? l[index] : l.next
      end
    end

    if block
      self.each do |elm|
        yield [elm, *tail.call]
      end
      nil
    else
      res = []
      self.each_entry { |elm| res << [elm, *tail.call] }
      res
    end
  end

  def cycle(n = nil, &block)
    return self.enum_for(:cycle, n) unless block
    unless n.nil?
      n = Topaz.convert_type(n, Fixnum, :to_int)
      return nil if n <= 0
    end

    buf = []
    self.each_entry do |e|
      buf << e
      yield e
    end
    return nil if buf.empty?

    if n
      (n - 1).times { buf.each(&block) }
    else
      while true
        buf.each(&block)
      end
    end
  end

  def grep(pattern, &block)
    ret = []
    if block
      self.each do |elm|
        if pattern === elm
          ret << yield(elm)
        end
      end
    else
      self.each do |elm|
        if pattern === elm
          ret << elm
        end
      end
    end
    ret
  end

  def chunk(initial_state = nil, &original_block)
    raise ArgumentError.new("no block given") unless original_block
    ::Enumerator.new do |yielder|
      previous = nil
      accumulate = []
      block = initial_state.nil? ? original_block : Proc.new{ |val| original_block.yield(val, initial_state.clone)}
      each do |val|
        key = block.yield(val)
        if key.nil? || (key.is_a?(Symbol) && key.to_s[0, 1] == "_")
          yielder.yield [previous, accumulate] unless accumulate.empty?
          accumulate = []
          previous = nil
          case key
          when nil, :_separator
          when :_alone
            yielder.yield [key, [val]]
          else
            raise RuntimeError.new("symbols beginning with an underscore are reserved")
          end
        else
          if previous.nil? || previous == key
            accumulate << val
          else
            yielder.yield [previous, accumulate] unless accumulate.empty?
            accumulate = [val]
          end
          previous = key
        end
      end
      yielder.yield [previous, accumulate] unless accumulate.empty?
    end
  end

  def slice_before(*args, &block)
    arg = nil
    if block
      raise ArgumentError.new("wrong number of arguments (#{args.size} for 0..1)") if args.size > 1
      if args.size == 1
        has_init = true
        arg = args[0]
      end
    else
      raise ArgumentError.new("wrong number of arguments (#{args.size} for 1)") if args.size > 1
      raise ArgumentError.new("wrong number of arguments (0 for 1)") if args.empty?
      arg = args[0]
      block = Proc.new{ |elem| arg === elem }
    end
    ::Enumerator.new do |yielder|
      init = arg.dup if has_init
      accumulator = nil
      each do |elem|
        start_new = has_init ? block.yield(elem, init) : block.yield(elem)
        if start_new
          yielder.yield accumulator if accumulator
          accumulator = [elem]
        else
          accumulator ||= []
          accumulator << elem
        end
      end
      yielder.yield accumulator if accumulator
    end
  end
end
