"""
Copyright (c) 2013, Jurriaan Bremer
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
* Neither the name of the darm developer(s) nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
from ctypes import cdll, Structure, byref, POINTER, create_string_buffer
from ctypes import c_uint16, c_int32, c_uint32, c_char_p


class _Base:
    def __init__(self, idx):
        self.idx = idx

    def __int__(self):
        return self.idx

    def __nonzero__(self):
        return self.idx != self._nonzero

    __bool__ = __nonzero__


class Condition(_Base):
    _nonzero = -1

    def __str__(self):
        return _lib.armv7_condition_by_index(self.idx)

    def __repr__(self):
        return 'C_%s' % self.__str__()


class Instruction(_Base):
    _nonzero = 0

    def __str__(self):
        return _lib.armv7_mnemonic_by_index(self.idx)

    def __repr__(self):
        return 'I_%s' % self.__str__()


class Register(_Base):
    _nonzero = -1

    def __str__(self):
        return _lib.armv7_register_by_index(self.idx)

    def __repr__(self):
        return self.__str__()


class Encoding(_Base):
    _nonzero = 0

    def __str__(self):
        return _lib.armv7_enctype_by_index(self.idx)

    def __repr__(self):
        return 'T_%s' % self.__str__()


class Shift:
    _types = 'LSL', 'LSR', 'ASR', 'ROR'

    def __init__(self, is_reg, type_, Rs, shift):
        self.is_reg = is_reg
        self.type_ = type_
        self.Rs = Rs
        self.shift = shift

    def __str__(self):
        if self.is_reg:
            return '%s %s' % (self._types[self.type_], self.Rs)
        else:
            return '%s #%d' % (self._types[self.type_], self.shift)

    def __repr__(self):
        if self.is_reg:
            return 'Shift(is_reg=%s, type_=%s, Rs=%s)' % \
                (self.is_reg, bin(self.type_), self.Rs)
        else:
            return 'Shift(is_reg=%s, type_=%s, shift=%d)' % \
                (self.is_reg, bin(self.type_), self.shift)

    def __nonzero__(self):
        return bool(self.is_reg or self.type_ or self.Rs or self.shift)


class RegisterList:
    def __init__(self, reglist):
        self.reglist = reglist

    def __str__(self):
        buf = create_string_buffer(64)
        _lib.armv7_reglist(self.reglist, buf)
        return buf.value

    def __nonzero__(self):
        return self.reglist != 0


def flag(v):
    """Boolean flag.

    http://thedailywtf.com/Articles/What_Is_Truth_0x3f_.aspx

    """
    return {0: False, 1: True, 2: None}[v]


class _Darm(Structure):
    _fields_ = [
        ('w', c_uint32),
        ('instr', c_uint32),
        ('instr_type', c_uint32),
        ('cond', c_uint32),
        ('S', c_uint32),
        ('E', c_uint32),
        ('F', c_uint32),
        ('M', c_uint32),
        ('N', c_uint32),
        ('option', c_uint32),
        ('U', c_uint32),
        ('H', c_uint32),
        ('P', c_uint32),
        ('R', c_uint32),
        ('T', c_uint32),
        ('W', c_uint32),
        ('Rd', c_int32),
        ('Rn', c_int32),
        ('Rm', c_int32),
        ('Ra', c_int32),
        ('Rt', c_int32),
        ('RdHi', c_int32),
        ('RdLo', c_int32),
        ('imm', c_uint32),
        ('type_', c_uint32),
        ('shift_is_reg', c_uint32),
        ('Rs', c_int32),
        ('shift', c_uint32),
        ('lsb', c_uint32),
        ('width', c_uint32),
        ('reglist', c_uint16),
    ]


class Darm:
    _flags = 'S', 'E', 'F', 'M', 'N', 'U', 'H', 'P', 'R', 'T', 'W'
    _regs = 'Rd', 'Rn', 'Rm', 'Ra', 'Rt', 'RdHi', 'RdLo'

    def __init__(self, d):
        self.w = d.w
        self.instr = Instruction(d.instr)
        self.instr_type = Encoding(d.instr_type)
        self.cond = Condition(d.cond)

        for x in self._flags:
            setattr(self, x, flag(getattr(d, x)))

        for x in self._regs:
            r = getattr(d, x)
            setattr(self, x, Register(r) if r >= 0 else None)

        self.option = d.option
        self.imm = d.imm
        self.shift = Shift(d.shift_is_reg,
                           d.type_,
                           Register(d.Rs) if d.Rs >= 0 else None,
                           d.shift)
        self.lsb = d.lsb
        self.width = d.width
        self.reglist = RegisterList(d.reglist)

    def __repr__(self):
        g = lambda x: getattr(self, x)

        args = []

        # registers
        args += ['%s=%s' % (r, g(r)) for r in self._regs if not g(r) is None]

        # flags
        args += ['%s=%s' % (r, g(r)) for r in self._flags if not g(r) is None]

        # other flags
        if self.option != 16:
            args.append('option=%s' % bin(self.option))

        if self.imm:
            args.append('imm=%s' % (str(self.imm)
                                    if self.imm < 0x1000 else
                                    hex(self.imm)[2:]))

        if self.shift:
            args.append(repr(self.shift))

        if self.lsb or self.width:
            args += ['lsb=%d' % self.lsb, 'width=%d' % self.width]

        if self.reglist:
            args.append('reglist=%s' % str(self.reglist))

        args = ', ' + ', '.join(args) if args else ''
        return 'Darm(instr=%s, instr_type=%s, cond=%s%s)' % \
            (repr(self.instr), repr(self.instr_type), repr(self.cond), args)


def disasm(w):
    d = _Darm()
    ret = _lib.armv7_disassemble(byref(d), w)
    return Darm(d) if ret == 0 else None


def _set_func(name, restype, *argtypes):
    getattr(_lib, name).restype = restype
    getattr(_lib, name).argtypes = argtypes

_lib = cdll.LoadLibrary('libdarm.so')
_set_func('armv7_disassemble', c_int32, POINTER(_Darm), c_uint32)
_set_func('armv7_mnemonic_by_index', c_char_p, c_uint32)
_set_func('armv7_enctype_by_index', c_char_p, c_uint32)
_set_func('armv7_register_by_index', c_char_p, c_int32)
_set_func('armv7_condition_by_index', c_char_p, c_int32)
_set_func('armv7_reglist', None, c_uint16, c_char_p)