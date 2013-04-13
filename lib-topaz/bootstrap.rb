# This file loads all the ruby kernel code in its directory

lib_topaz = File.dirname(__FILE__)
load_bootstrap = proc do |file|
  load(File.join(lib_topaz, file))
end

load_bootstrap.call("topaz.rb")
load_bootstrap.call("array.rb")
load_bootstrap.call("class.rb")
load_bootstrap.call("comparable.rb")
load_bootstrap.call("enumerable.rb")
load_bootstrap.call("enumerator.rb")
load_bootstrap.call("file.rb")
load_bootstrap.call("fixnum.rb")
load_bootstrap.call("hash.rb")
load_bootstrap.call("integer.rb")
load_bootstrap.call("io.rb")
load_bootstrap.call("kernel.rb")
load_bootstrap.call("numeric.rb")
load_bootstrap.call("process.rb")
load_bootstrap.call("range.rb")
load_bootstrap.call("random.rb")
load_bootstrap.call("string.rb")
load_bootstrap.call("symbol.rb")
load_bootstrap.call("thread.rb")
load_bootstrap.call("top_self.rb")
