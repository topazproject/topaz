module Enumerable
  def first(*args)
    if args.empty?
      self.each { |e| return e }
      nil
    else
      take(*args)
    end
  end

  def map(&block)
    return self.enum_for(:map) unless block
    result = []
    self.each do |x|
      result << (yield x)
    end
    result
  end

  alias collect map

  def inject(*args)
    dropped = 0
    meth = nil
    case args.length
    when 0
      memo = self.first
      dropped = 1
    when 1
      memo = args[0]
    when 2
      memo = args[0]
      meth = args[1]
    end
    self.drop(dropped).each do |x|
      if meth
        memo = memo.send(meth, x)
      else
        memo = (yield memo, x)
      end
    end
    memo
  end

  alias reduce inject

  def each_with_index(&block)
    return self.enum_for(:each_with_index) if !block
    i = 0
    self.each do |obj|
      yield obj, i
      i += 1
    end
  end

  def each_with_object(memo, &block)
    return self.enum_for(:each_with_object, memo) unless block
    self.each do |elm|
      yield elm, memo
    end
    memo
  end

  def all?(&block)
    self.each do |obj|
      return false unless (block ? block.call(obj) : obj)
    end
    true
  end

  def any?(&block)
    self.each do |obj|
      return true if (block ? block.call(obj) : obj)
    end
    false
  end

  def select(&block)
    return self.enum_for(:select) unless block
    result = []
    self.each do |o|
      if block.call(o)
        result << o
      end
    end
    result
  end

  alias :find_all :select

  def include?(obj)
    self.each do |o|
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
    self.each do |o|
      unless dropping && yield(o)
        result << o
        dropping = false
      end
    end
    result
  end

  def to_a
    result = []
    self.each do |i|
      result << i
    end
    result
  end
  alias entries to_a

  def detect(ifnone = nil, &block)
    return self.enum_for(:detect, ifnone) unless block
    self.each do |o|
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
      self.each do |o|
        result << o
        break if result.size == n
      end
    end
    result
  end

  def take_while(&block)
    return self.enum_for(:take_while) unless block
    result = []
    self.each do |o|
      break unless yield(o)
      result << o
    end
    result
  end

  def reject(&block)
    return self.enum_for(:reject) unless block
    result = []
    self.each do |o|
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
    self.each do |e|
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
    self.each do |e|
      c += 1 if block ? yield(e) : e
    end
    c == 1
  end

  def none?(&block)
    self.each do |e|
      return false if block ? yield(e) : e
    end
    true
  end

  def group_by(&block)
    return self.enum_for(:group_by) unless block
    h = {}
    self.each do |e|
      v = yield e
      a = h.fetch(v) { |v| h[v] = [] }
      a << e
    end
    h
  end

  def find_index(obj = nil, &block)
    return self.enum_for(:find_index) if !obj && !block
    each_with_index do |e, i|
      return i if obj ? (e == obj) : block.call(e)
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
    self.each do |e|
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
      if v.respond_to?(:to_ary) && ary = Array.try_convert(v)
        out.concat(ary)
      else
        out << v
      end
    end
    out
  end
  alias flat_map collect_concat
end
