module Topaz
  class Array
    def self.flatten(array, out, level)
      modified = nil
      Thread.current.recursion_guard(:array_flatten, array) do
        array.each do |e|
          if level == 0
            out << e
          elsif e.respond_to?(:to_ary) && ary = ::Array.try_convert(e)
            modified = true
            flatten(ary, out, level - 1)
          else
            out << e
          end
        end
        return modified
      end
      raise ArgumentError, "tried to flatten recursive array"
    end
  end
end

class Topaz::Array::IdentityMap
  def initialize(array)
    @h = {}
    add(array)
  end

  def add(array)
    if @h.empty?
      array.each { |e| @h[e] = e }
    else
      array.each { |e| @h.fetch(e){|v| @h[v] = e } }
    end
  end

  def values
    @h.values
  end

  def include?(a)
    if b = @h[a]
      a.equal?(b) || a.eql?(b)
    end
  end

  def pop?(a)
    if b = @h.delete(a)
      a.equal?(b) || a.eql?(b)
    end
  end
end
