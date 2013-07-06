class MSpecScript
  Topaz = File.expand_path(File.dirname(__FILE__))
  Rubyspec = File.expand_path("../../rubyspec", __FILE__)

  MSpec.enable_feature :fiber
  core = ["#{Rubyspec}/core/",
          "^#{Rubyspec}/core/struct",
          "^#{Rubyspec}/core/string/chomp_spec.rb",
          "^#{Rubyspec}/core/process/detach_spec.rb",
          "^#{Rubyspec}/core/gc/profiler/",
          "^#{Rubyspec}/core/marshal/dump_spec.rb",
          "^#{Rubyspec}/core/marshal/load_spec.rb",
          "^#{Rubyspec}/core/marshal/restore_spec.rb",
          "^#{Rubyspec}/core/kernel/autoload_spec.rb",
          "^#{Rubyspec}/core/filetest",
          "^#{Rubyspec}/core/io/reopen_spec.rb",
          "^#{Rubyspec}/core/file/socket_spec.rb",
          "^#{Rubyspec}/core/numeric/to_c_spec.rb",
  ]

  language = [
    "#{Rubyspec}/language",
    # Block local variables: ``[].each {|a; b| }``
    "^#{Rubyspec}/language/block_spec.rb",
    # Posix character class: ``/[[:alnum:]]/``
    "^#{Rubyspec}/language/regexp/character_classes_spec.rb",
    # Required arg after *arg: ``def f(a, *b, c); end``
    "^#{Rubyspec}/language/send_spec.rb",
    # stringio: ``require 'stringio'``
    "^#{Rubyspec}/language/predefined_spec.rb",
    # Void expression: ``break true or false``
    "^#{Rubyspec}/language/or_spec.rb",
    # rubyspec/languages/fixtures/start.rb
    "^#{Rubyspec}/language/return_spec.rb",
  ]

  command_line = ["#{Rubyspec}/command_line"]

  library = ["#{Rubyspec}/library",
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
             "^#{Rubyspec}/library/zlib/"]

  set :tags_patterns, [
      [/#{Rubyspec}/, "#{Topaz}/spec/tags"],
      [/_spec.rb$/, '_tags.txt']
  ]

  set :files, core + language + library + command_line
end
