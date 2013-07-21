module Topaz
  def self.recursion_guard_outer(identifier, obj, &block)
    # We want to throw something less likely to be caught accidentally outside
    # our own code than the recursion identifier. Ideally this should be an
    # object that is unique to this particular recursion guard. Since doing
    # that properly requires pushing extra state all the way up into
    # ExecutionContext, we do this instead.
    throw_symbol = "__recursion_guard_#{identifier}".to_sym

    if Thread.current.in_recursion_guard?(identifier)
      Thread.current.recursion_guard(identifier, obj) do
        yield
        return false
      end
      throw(throw_symbol)
    else
      Thread.current.recursion_guard(identifier, obj) do
        catch(throw_symbol) do
          yield
          return false
        end
        return true
      end
    end
  end
end

lib_topaz = File.join(File.dirname(__FILE__), 'topaz')
load_bootstrap = proc do |file|
  load(File.join(lib_topaz, file))
end

load_bootstrap.call("array.rb")
