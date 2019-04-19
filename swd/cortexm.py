"""Cortex-Mx definitions
"""

import time
import swd.io.cortexm as _io_cm


class CortexMException(Exception):
    """CortexM general exception"""


class CortexMNotDetected(Exception):
    """Exception"""


class CortexM:
    """Definitions for Cortex-M MCUs"""

    REGISTERS = [
        'R0', 'R1', 'R2', 'R3', 'R4', 'R5',
        'R6', 'R7', 'R8', 'R9', 'R10', 'R11', 'R12',
        'SP', 'LR', 'PC', 'PSR', 'MSP', 'PSP']

    def create_io(self):
        """Create IO registers"""
        cpuid = _io_cm.Cpuid(self._swd)
        implementer = cpuid.cached.get_named('IMPLEMENTER')
        partno = cpuid.cached.get_named('PARTNO')
        if implementer != 'ARM' or partno is None:
            raise CortexMNotDetected(
                "Unknown MCU with CPUID: 0x%08x" % cpuid.cached.raw)
        self._swd.append_io({
            'CPUID': cpuid,
            'AIRCR': _io_cm.Aircr(self._swd),
            'DHCSR_W': _io_cm.DhcsrWrite(self._swd),
            'DHCSR_R': _io_cm.DhcsrRead(self._swd),
            'DEMCR': _io_cm.Demcr(self._swd),
        })

    def __init__(self, swd):
        self._swd = swd
        self.create_io()
        cpuid = self._swd.reg('CPUID')
        self._implementer = cpuid.cached.get_named('IMPLEMENTER')
        self._core = cpuid.cached.get_named('PARTNO')

    @property
    def swd(self):
        """Return instance of SWD"""
        return self._swd

    @property
    def implementer(self):
        """Return implementer name"""
        return self._implementer

    @property
    def core(self):
        """Return core name"""
        return self._core

    def info_str(self):
        """Return controller info string"""
        return "%s/%s" % (self._implementer, self._core)

    @classmethod
    def _get_reg_index(cls, reg):
        if reg.upper() not in cls.REGISTERS:
            raise CortexMException("Not a register")
        return cls.REGISTERS.index(reg)

    def get_reg(self, reg):
        """Read register"""
        return self._swd.get_reg(CortexM._get_reg_index(reg))

    def set_reg(self, reg, data):
        """Read register"""
        return self._swd.set_reg(CortexM._get_reg_index(reg), data)

    def get_reg_all(self):
        """Read all registers"""
        return dict(zip(CortexM.REGISTERS, self._swd.get_reg_all()))

    def reset(self):
        """Reset"""
        self._swd.reg('DEMCR').set_bits({
            'VC_CORERESET': False})
        self._swd.reg('AIRCR').set_bits({
            'VECTKEY': 'KEY',
            'SYSRESETREQ': True})
        time.sleep(.01)

    def reset_halt(self):
        """Reset and halt"""
        self.halt()
        self._swd.reg('DEMCR').set_bits({
            'VC_CORERESET': True})
        self._swd.reg('AIRCR').set_bits({
            'VECTKEY': 'KEY',
            'SYSRESETREQ': True})
        time.sleep(.01)

    def halt(self):
        """Halt"""
        self._swd.reg('DHCSR_W').set_bits({
            'DBGKEY': 'KEY',
            'C_DEBUGEN': True,
            'C_HALT': True})

    def step(self):
        """Step"""
        self._swd.reg('DHCSR_W').set_bits({
            'DBGKEY': 'KEY',
            'C_DEBUGEN': True,
            'C_STEP': True})

    def run(self):
        """Enable debug"""
        self._swd.reg('DHCSR_W').set_bits({
            'DBGKEY': 'KEY',
            'C_DEBUGEN': True})

    def nodebug(self):
        """Disable debug"""
        self._swd.reg('DHCSR_W').set_bits({
            'DBGKEY': 'KEY',
            'C_DEBUGEN': False})

    def is_halted(self):
        """check if core is halted"""
        return self._swd.reg('DHCSR_R').get('S_HALT')
