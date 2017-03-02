module FFI
  class Pointer
    def NULL.==(other)
      other.equal? nil
    end
    def NULL.method_missing(meth_id, *args)
      meth_name = meth_id.id2name
      if meth_name.start_with? 'read'
        raise NullPointerError.new("read attempt on NULL pointer")
      end
      if meth_name.start_with? 'write'
        raise NullPointerError.new("write attempt on NULL pointer")
      end
      raise NoMethodError.new("undefined method `#{meth_name}' for #{self}")
    end

    def write_array_of_uint32(ary)
      write_string(ary.pack("L#{ary.size}"))
    end
  end
end
