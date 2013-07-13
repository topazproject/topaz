class Topaz::Rubinius
  L64 = true

  class Type
    def self.coerce_to(obj, type, method)
      if obj.kind_of? type
        obj.send method
      else
        obj
      end
    end

    def self.binary_string(str)
      str
    end

    def self.object_kind_of?(obj, cls)
      obj.kind_of? cls
    end

    def self.infect(obj, other)
      obj
    end

    def self.convert_to_names(list)
      list
    end

    def self.object_encoding(obj)
      nil
    end

    def self.object_class(obj)
      obj.class
    end

    def self.module_inspect(mod)
      mod.inspect
    end
  end

  class LookupTable < Hash
  end

  def self.extended_modules(obj)
    []
  end
end
