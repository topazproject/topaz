class MSpecScript
  Topaz = File.expand_path(File.dirname(__FILE__))
  Rubyspec = File.expand_path("../../rubyspec", __FILE__)

  MSpec.enable_feature :fiber
  MSpec.enable_feature :fork
  MSpec.enable_feature :encoding
  core = [
    "#{Rubyspec}/core/",
    # Struct: ``Struct.new(:field)``
    "^#{Rubyspec}/core/string/chomp_spec.rb",
    # timeout: ``require 'timeout'``
    "^#{Rubyspec}/core/process/detach_spec.rb",
    # GC: ``GC``
    "^#{Rubyspec}/core/gc/profiler/",
    # openssl: ``require 'openssl'``
    "^#{Rubyspec}/core/marshal/dump_spec.rb",
    # openssl: ``require 'openssl'``
    "^#{Rubyspec}/core/marshal/load_spec.rb",
    # openssl: ``require 'openssl'``
    "^#{Rubyspec}/core/marshal/restore_spec.rb",
    # autoload: ``autoload :Class, "file.rb"``
    "^#{Rubyspec}/core/kernel/autoload_spec.rb",
    # FileTest: ``FileTest``
    "^#{Rubyspec}/core/filetest",
    # fcntl: ``require 'fcntl'``
    "^#{Rubyspec}/core/io/reopen_spec.rb",
    # socket: ``require 'socket'``
    "^#{Rubyspec}/core/file/socket_spec.rb",
    # rubyspecs/core/io/fixtures/file_types:
    #   `find /dev /devices -type b` returns nil
    #   -> NoMethodError: undefined method `split' for NilClass
    "^#{Rubyspec}/core/file/ftype_spec.rb",
    "^#{Rubyspec}/core/file/stat/ftype_spec.rb",
    # Rational: ``Rational(2, 3)``
    "^#{Rubyspec}/core/numeric/to_c_spec.rb",
  ]

  language = [
    "#{Rubyspec}/language",
    # Required block arg after *args: ``f {|*a, b| }``
    "^#{Rubyspec}/language/block_spec.rb",
    # Posix character class: ``/[[:alnum:]]/``
    "^#{Rubyspec}/language/regexp/character_classes_spec.rb",
    # Required arg after *arg: ``def f(a, *b, c); end``
    "^#{Rubyspec}/language/send_spec.rb",
    # stringio: ``require 'stringio'``
    "^#{Rubyspec}/language/predefined_spec.rb",
    # AttributeError: 'File' object has no attribute 'compile_defined'
    "^#{Rubyspec}/language/defined_spec.rb",
    # no real reason found (results in an Aborted (core dumped))
    #   AssertionError in Parser_combine_send_block ?
    "^#{Rubyspec}/language/return_spec.rb",
    # command_asgn_lhs_equal_command_asgn
    "^#{Rubyspec}/language/variables_spec.rb",
  ]

  command_line = ["#{Rubyspec}/command_line"]

  library = [
    "#{Rubyspec}/library",
    "^#{Rubyspec}/library/abbrev/abbrev_spec.rb",
    "^#{Rubyspec}/library/logger/application/new_spec.rb",
    "^#{Rubyspec}/library/base64/",
    "^#{Rubyspec}/library/bigdecimal/",
    "^#{Rubyspec}/library/cgi/",
    "^#{Rubyspec}/library/complex/",
    "^#{Rubyspec}/library/conditionvariable/",
    "^#{Rubyspec}/library/csv/",
    "^#{Rubyspec}/library/date/",
    "^#{Rubyspec}/library/datetime/",
    "^#{Rubyspec}/library/delegate/",
    "^#{Rubyspec}/library/digest/",
    "^#{Rubyspec}/library/drb/",
    "^#{Rubyspec}/library/erb/",
    "^#{Rubyspec}/library/etc/",
    "^#{Rubyspec}/library/expect/expect_spec.rb",
    "^#{Rubyspec}/library/find/",
    "^#{Rubyspec}/library/getoptlong/",
    "^#{Rubyspec}/library/iconv/",
    "^#{Rubyspec}/library/ipaddr/",
    "^#{Rubyspec}/library/logger/",
    "^#{Rubyspec}/library/mathn/",
    "^#{Rubyspec}/library/matrix/",
    "^#{Rubyspec}/library/net/",
    "^#{Rubyspec}/library/observer/",
    "^#{Rubyspec}/library/open3/",
    "^#{Rubyspec}/library/openssl/",
    "^#{Rubyspec}/library/openstruct/",
    "^#{Rubyspec}/library/pathname/",
    "^#{Rubyspec}/library/prime/",
    "^#{Rubyspec}/library/queue/",
    "^#{Rubyspec}/library/resolv/",
    "^#{Rubyspec}/library/rexml/",
    "^#{Rubyspec}/library/scanf/",
    "^#{Rubyspec}/library/securerandom/",
    "^#{Rubyspec}/library/set/",
    "^#{Rubyspec}/library/shellwords/",
    "^#{Rubyspec}/library/singleton/",
    "^#{Rubyspec}/library/socket/",
    "^#{Rubyspec}/library/stringio/",
    "^#{Rubyspec}/library/stringscanner/",
    "^#{Rubyspec}/library/syslog/",
    "^#{Rubyspec}/library/tempfile/",
    "^#{Rubyspec}/library/time/",
    "^#{Rubyspec}/library/timeout/",
    "^#{Rubyspec}/library/tmpdir/",
    "^#{Rubyspec}/library/uri/",
    "^#{Rubyspec}/library/weakref/",
    "^#{Rubyspec}/library/win32ole/",
    "^#{Rubyspec}/library/yaml/",
    "^#{Rubyspec}/library/zlib/"
  ]

  set :tags_patterns, [
      [/#{Rubyspec}/, "#{Topaz}/spec/tags"],
      [/_spec.rb$/, '_tags.txt']
  ]

  set :files, core + language + library + command_line
end
