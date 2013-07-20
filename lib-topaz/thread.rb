class Thread
  class << self
    def abort_on_exception=(value)
      @abort_on_exception = !!value
    end

    def abort_on_exception
      @abort_on_exception ||= false
    end
  end

  def abort_on_exception=(value)
    @abort_on_exception = !!value
  end

  def abort_on_exception
    @abort_on_exception ||= (Thread.abort_on_exception || false)
  end

  def recursion_guard_outer(identifier, obj, &block)
    # We want to throw something less likely to be caught accidentally outside
    # our own code than the recursion identifier. Ideally this should be an
    # object that is unique to this particular recursion guard. Since doing
    # that properly requires pushing extra state all the way up into
    # ExecutionContext, we do this instead.
    throw_symbol = "__recursion_guard_#{identifier}".to_sym

    if self.in_recursion_guard?(identifier)
      self.recursion_guard(identifier, obj) do
        yield
        return false
      end
      throw(throw_symbol)
    else
      self.recursion_guard(identifier, obj) do
        catch(throw_symbol) do
          yield
          return false
        end
        return true
      end
    end
  end
end
