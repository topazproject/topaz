from __future__ import absolute_import

import math

from rpython.rlib import rfloat

from topaz.module import ModuleDef, ClassDef
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate


class Math(object):
    moduledef = ModuleDef("Math")

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, "PI", space.newfloat(math.pi))
        space.set_const(w_mod, "E", space.newfloat(math.e))
        space.set_const(w_mod, "DomainError", space.getclassfor(W_DomainError))

    @moduledef.function("acos", value="strictfloat")
    def method_acos(self, space, value):
        return space.newfloat(math.acos(value))

    @moduledef.function("acosh", value="strictfloat")
    def method_acosh(self, space, value):
        try:
            res = math.acosh(value)
        except ValueError:
            raise space.error(space.getclassfor(W_DomainError), 'Numerical argument is out of domain - "acosh"')
        return space.newfloat(res)

    @moduledef.function("asin", value="strictfloat")
    def method_asin(self, space, value):
        return space.newfloat(math.asin(value))

    @moduledef.function("asinh", value="strictfloat")
    def method_asinh(self, space, value):
        return space.newfloat(math.asinh(value))

    @moduledef.function("atan", value="strictfloat")
    def method_atan(self, space, value):
        return space.newfloat(math.atan(value))

    @moduledef.function("atan2", value1="strictfloat", value2="strictfloat")
    def method_atan2(self, space, value1, value2):
        return space.newfloat(math.atan2(value1, value2))

    @moduledef.function("atanh", value="strictfloat")
    def method_atanh(self, space, value):
        try:
            res = math.atanh(value)
        except ValueError:
            if value == 1.0 or value == -1.0:
                # produce an infinity with the right sign
                res = rfloat.copysign(rfloat.INFINITY, value)
            else:
                raise space.error(space.getclassfor(W_DomainError), 'Numerical argument is out of domain - "atanh"')
        return space.newfloat(res)

    @moduledef.function("cbrt", value="strictfloat")
    def method_cbrt(self, space, value):
        if value < 0:
            return space.newfloat(-math.pow(-value, 1.0 / 3.0))
        else:
            return space.newfloat(math.pow(value, 1.0 / 3.0))

    @moduledef.function("cos", value="strictfloat")
    def method_cos(self, space, value):
        return space.newfloat(math.cos(value))

    @moduledef.function("cosh", value="strictfloat")
    def method_cosh(self, space, value):
        try:
            res = math.cosh(value)
        except OverflowError:
            res = rfloat.copysign(rfloat.INFINITY, value)
        return space.newfloat(res)

    @moduledef.function("exp", value="strictfloat")
    def method_exp(self, space, value):
        return space.newfloat(math.exp(value))

    @moduledef.function("frexp", value="strictfloat")
    def method_frexp(self, space, value):
        mant, exp = math.frexp(value)
        w_mant = space.newfloat(mant)
        w_exp = space.newint(exp)
        return space.newarray([w_mant, w_exp])

    @moduledef.function("gamma", value="strictfloat")
    def method_gamma(self, space, value):
        try:
            res = rfloat.gamma(value)
        except ValueError:
            if value == 0.0:
                # produce an infinity with the right sign
                res = rfloat.copysign(rfloat.INFINITY, value)
            else:
                raise space.error(space.getclassfor(W_DomainError), 'Numerical argument is out of domain - "gamma"')
        except OverflowError:
            res = rfloat.INFINITY
        return space.newfloat(res)

    @moduledef.function("lgamma", value="strictfloat")
    def method_lgamma(self, space, value):
        try:
            res = rfloat.lgamma(value)
        except (ValueError, OverflowError):
            res = rfloat.INFINITY
        gamma = (1 if value == -1 or math.isnan(value) else
                 space.float_w(space.send(self, "gamma", [space.newfloat(value)])))
        sign = 1 if gamma > 0 else -1 if gamma < 0 else 0
        return space.newarray([space.newfloat(res), space.newint(sign)])

    @moduledef.function("hypot", value1="strictfloat", value2="strictfloat")
    def method_hypot(self, space, value1, value2):
        return space.newfloat(math.hypot(value1, value2))

    @moduledef.function("ldexp", value1="strictfloat", value2="int")
    def method_ldexp(self, space, value1, value2):
        return space.newfloat(math.ldexp(value1, value2))

    @moduledef.function("log", value="strictfloat", base="strictfloat")
    def method_log(self, space, value, base=math.e):
        try:
            res = 0.0
            if base == math.e:
                res = math.log(value)
            else:
                res = math.log(value) / math.log(base)
        except ValueError:
            if value == 0.0:
                res = float(-rfloat.INFINITY)
            else:
                raise space.error(space.getclassfor(W_DomainError), 'Numerical argument is out of domain - "log"')

        return space.newfloat(res)

    @moduledef.function("log10", value="strictfloat")
    def method_log10(self, space, value):
        try:
            res = math.log10(value)
        except ValueError:
            if value == 0.0:
                res = float(-rfloat.INFINITY)
            else:
                raise space.error(space.getclassfor(W_DomainError), 'Numerical argument is out of domain - "log10"')

        return space.newfloat(res)

    @moduledef.function("log2", value="strictfloat")
    def method_log2(self, space, value):
        try:
            res = math.log(value) / math.log(2)
        except ValueError:
            if value == 0.0:
                res = float(-rfloat.INFINITY)
            else:
                raise space.error(space.getclassfor(W_DomainError), 'Numerical argument is out of domain - "log2"')

        return space.newfloat(res)

    @moduledef.function("sin", value="strictfloat")
    def method_sin(self, space, value):
        return space.newfloat(math.sin(value))

    @moduledef.function("sinh", value="strictfloat")
    def method_sinh(self, space, value):
        try:
            res = math.sinh(value)
        except OverflowError:
            res = rfloat.copysign(rfloat.INFINITY, value)
        return space.newfloat(res)

    @moduledef.function("sqrt", value="strictfloat")
    def method_sqrt(self, space, value):
        return space.newfloat(math.sqrt(value))

    @moduledef.function("tan", value="strictfloat")
    def method_tan(self, space, value):
        try:
            res = math.tan(value)
        except ValueError:
            res = rfloat.NAN
        return space.newfloat(res)

    @moduledef.function("tanh", value="strictfloat")
    def method_tanh(self, space, value):
        return space.newfloat(math.tanh(value))

    @moduledef.function("erf", value="strictfloat")
    def method_erf(self, space, value):
        return space.newfloat(rfloat.erf(value))

    @moduledef.function("erfc", value="strictfloat")
    def method_erfc(self, space, value):
        return space.newfloat(rfloat.erfc(value))


class W_DomainError(W_StandardError):
    classdef = ClassDef("Math::DomainError", W_StandardError.classdef)
    method_allocate = new_exception_allocate(classdef)
