#
# Copyright (C) 2008-2010 Wayne Meissner
# All rights reserved.
#
# This file is part of ruby-ffi.
#
# This code is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3 only, as
# published by the Free Software Foundation.
#
# This code is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# version 3 for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with this work.  If not, see <http://www.gnu.org/licenses/>.
#

# see {file:README}
module FFI

  # @param [Type, DataConverter, Symbol] old type definition used by {FFI.find_type}
  # @param [Symbol] add new type definition's name to add
  # @return [Type]
  # Add a definition type to type definitions.
  def self.typedef(old, add)
    TypeDefs[add] = self.find_type(old)
  end

  # (see FFI.typedef)
  def self.add_typedef(old, add)
    typedef old, add
  end


  # @param [Type, DataConverter, Symbol] name
  # @param [Hash] type_map if nil, {FFI::TypeDefs} is used
  # @return [Type]
  # Find a type in +type_map+ ({FFI::TypeDefs}, by default) from
  # a type objet, a type name (symbol). If +name+ is a {DataConverter},
  # a new {Type::Mapped} is created.
  def self.find_type(name, type_map = nil)
    if name.is_a?(Type)
      name

    elsif type_map && type_map.has_key?(name)
      type_map[name]

    elsif TypeDefs.has_key?(name)
      TypeDefs[name]

    elsif name.is_a?(DataConverter)
      (type_map || TypeDefs)[name] = Type::Mapped.new(name)
    
    else
      raise TypeError, "unable to resolve type '#{name}'"
    end
  end

  # DIFF: simplified the original code
  Type.constants.each do |typename|
    TypeDefs[typename.downcase] = Type.const_get(typename)
  end

  class StrPtrConverter
    extend DataConverter
    native_type Type::POINTER

    # @param [Pointer] val
    # @param [] ctx
    # @return [Array(String, Pointer)]
    # Returns a [ String, Pointer ] tuple so the C memory for the string can be freed
    def self.from_native(val, ctx)
      [ val.null? ? nil : val.get_string(0), val ]
    end

  end

  typedef(StrPtrConverter, :strptr)

  # @param type +type+ is an instance of class accepted by {FFI.find_type}
  # @return [Numeric]
  # Get +type+ size, in bytes.
  def self.type_size(type)
    find_type(type).size
  end

  # Load all the platform dependent types
  begin
    File.open(File.join(Platform::CONF_DIR, 'types.conf'), "r") do |f|
      prefix = "rbx.platform.typedef."
      f.each_line { |line|
        if line.index(prefix) == 0
          new_type, orig_type = line.chomp.slice(prefix.length..-1).split(/\s*=\s*/)
          typedef(orig_type.to_sym, new_type.to_sym)
        end
      }
    end
    typedef :pointer, :caddr_t
  rescue Errno::ENOENT
  end
end
