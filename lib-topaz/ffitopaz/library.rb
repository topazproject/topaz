module FFI
  module Library
    def attachments
        @attachments = {} if not instance_variable_defined?(:@attachments)
        return @attachments
    end
    def method_missing(meth_id, *args)
      return attachments[meth_id].call(*args) if attachments.include? meth_id
      raise NoMethodError.new("undefined method `#{meth_id}' for #{self}")
    end
  end
end
