"""Oxygen-machine HAL and MOCK adapter."""

from enum import Enum


class OxygenStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"
    FAULT = "FAULT"


class OxygenMachineInterface:
    def start(self) -> bool:
        raise NotImplementedError

    def stop(self) -> bool:
        raise NotImplementedError

    def status(self) -> OxygenStatus:
        raise NotImplementedError


class MockOxygenMachine(OxygenMachineInterface):
    """MOCK device; no GPIO, relay, contactor, or motor is accessed."""

    def __init__(self) -> None:
        self._status = OxygenStatus.OFF
        self.command_log: list[str] = []

    def start(self) -> bool:
        if self._status is OxygenStatus.FAULT:
            return False
        self._status = OxygenStatus.ON
        self.command_log.append("START")
        return True

    def stop(self) -> bool:
        if self._status is OxygenStatus.FAULT:
            return False
        self._status = OxygenStatus.OFF
        self.command_log.append("STOP")
        return True

    def status(self) -> OxygenStatus:
        return self._status

    def inject_fault(self) -> None:
        self._status = OxygenStatus.FAULT

