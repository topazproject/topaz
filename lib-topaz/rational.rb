class Rational < Numeric
  def initialize(nom, denom)
    @nominator = nom
    @denominator = denom
  end
end

module Kernel
  def Rational(nom, denom=1)
    Rational.new(
      Topaz.convert_type(nom, Fixnum, :to_int),
      Topaz.convert_type(nom, Fixnum, :to_int)
    )
  end
end
