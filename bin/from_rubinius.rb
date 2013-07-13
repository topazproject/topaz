#!/usr/bin/env ruby

while gets
  $_.gsub! /Rubinius::/, "Topaz::Rubinius::"
  $_.gsub! /Rubinius\./, "Topaz::Rubinius."
  $_.gsub! /\.__instance_variables__/, ".class.instance_variables.clear"
  print $_
end
