# On MRI, this file gets created by mkconfig.rb when ruby is
# built. Our config is adapted from Rubinius.

unless RUBY_ENGINE == "topaz"
  raise "Looks like you loaded the Topaz rbconfig, but this is not Topaz."
end

module RbConfig
  prefix = File.dirname(File.dirname(__FILE__))

  CONFIG = {}

  CONFIG["bindir"]             = File.join(prefix, "bin")
  CONFIG["ruby_install_name"]  = RUBY_ENGINE.dup
  CONFIG["RUBY_INSTALL_NAME"]  = RUBY_ENGINE.dup
  CONFIG["host_os"]            = RUBY_PLATFORM.split("-")[-1]
  CONFIG["exeext"]             = ""
  CONFIG["EXEEXT"]             = ""
end

Config = RbConfig
