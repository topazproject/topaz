fails:Fixnum#<< with n << m returns 0 when m < 0 and m is a Bignum
fails:Fixnum#<< with n << m returns a Bignum == fixnum_max() * 2 when fixnum_max() << 1 and n > 0
fails:Fixnum#<< with n << m returns a Bignum == fixnum_min() * 2 when fixnum_min() << 1 and n < 0
