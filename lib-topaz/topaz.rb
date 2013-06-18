module Topaz
end

lib_topaz = File.join(File.dirname(__FILE__), 'topaz')
load_bootstrap = proc do |file|
  load(File.join(lib_topaz, file))
end

load_bootstrap.call("array.rb")
