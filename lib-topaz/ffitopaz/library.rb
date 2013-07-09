module FFI
  module Library
    Attachments = {}
    def self.method_missing(meth_id, *args)
      return Attachments[meth_id].call(*args) if Attachments.include? meth_id
      raise NoMethodError.new("undefined method `#{meth_id}' for #{self}")
    end
  end
end
