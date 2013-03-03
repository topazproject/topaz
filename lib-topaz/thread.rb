class Thread
  def recursion_guard_outer(identifier, obj, &block)
    # We want to throw something less likely to be caught accidentally outside
    # our own code than the recursion identifier. Ideally this should be an
    # object that is unique to this particular recursion guard. Since doing
    # that properly requires pushing extra state all the way up into
    # ExecutionContext, we do this instead.
    throw_symbol = "__recursion_guard_#{identifier}".to_sym

    if self.in_recursion_guard?(identifier)
      self.recursion_guard(identifier, obj) do |recursion|
        if !recursion
          yield(false)
        else
          throw(throw_symbol)
        end
      end
    else
      self.recursion_guard(identifier, obj) do |recursion|
        catch(throw_symbol) do
          return yield(false)
        end
        return yield(true)
      end
    end
  end
end
