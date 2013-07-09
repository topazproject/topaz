module FFI
  module Library
    Attachments = {}
    def self.method_missing(meth_id, *args)
      if const_defined?(:Attachments) and Attachments.include? meth_id
        return Attachments[meth_id].call(*args)
      else
        raise NoMethodError.new("undefined method `#{meth_id}' for #{self}")
      end
    end
  end
end
