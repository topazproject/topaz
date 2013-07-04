module FFI
  class Pointer
    def NULL.==(other)
      other.equal? nil
    end
  end
end
