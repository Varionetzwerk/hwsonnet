"""Hardware sensors collector — temperatures, fans, voltages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import psutil

from src.utils.logger import logger


@dataclass
class TempSensor:
    label: str = ""
    current: float = 0.0
    high: Optional[float] = None
    critical: Optional[float] = None
    chip: str = ""


@dataclass
class FanSensor:
    label: str = ""
    rpm: int = 0
    chip: str = ""


@dataclass
class BatterySensor:
    percent: float = 0.0
    plugged_in: bool = True
    seconds_left: Optional[float] = None
    status: str = "N/A"


@dataclass
class SensorsInfo:
    temperatures: list[TempSensor] = field(default_factory=list)
    fans: list[FanSensor] = field(default_factory=list)
    battery: Optional[BatterySensor] = None


class SensorsCollector:
    """Reads hardware sensors via psutil (which wraps lm_sensors / hwmon)."""

    def collect_static(self) -> SensorsInfo:
        return self._collect_all()

    def collect_dynamic(self, info: SensorsInfo) -> None:
        fresh = self._collect_all()
        info.temperatures = fresh.temperatures
        info.fans = fresh.fans
        info.battery = fresh.battery

    # ------------------------------------------------------------------ #

    def _collect_all(self) -> SensorsInfo:
        info = SensorsInfo()
        info.temperatures = self._collect_temps()
        info.fans = self._collect_fans()
        info.battery = self._collect_battery()
        return info

    def _collect_temps(self) -> list[TempSensor]:
        sensors: list[TempSensor] = []
        try:
            all_temps = psutil.sensors_temperatures()
            for chip_name, entries in all_temps.items():
                for entry in entries:
                    sensors.append(
                        TempSensor(
                            label=entry.label or chip_name,
                            current=entry.current,
                            high=entry.high,
                            critical=entry.critical,
                            chip=chip_name,
                        )
                    )
        except Exception as exc:
            logger.debug("Temperature sensor error: %s", exc)
        return sensors

    def _collect_fans(self) -> list[FanSensor]:
        fans: list[FanSensor] = []
        try:
            all_fans = psutil.sensors_fans()
            for chip_name, entries in all_fans.items():
                for entry in entries:
                    fans.append(
                        FanSensor(
                            label=entry.label or f"Fan {len(fans) + 1}",
                            rpm=entry.current,
                            chip=chip_name,
                        )
                    )
        except Exception as exc:
            logger.debug("Fan sensor error: %s", exc)
        return fans

    def _collect_battery(self) -> Optional[BatterySensor]:
        try:
            bat = psutil.sensors_battery()
            if bat is None:
                return None
            status = "Charging" if bat.power_plugged else "Discharging"
            return BatterySensor(
                percent=bat.percent,
                plugged_in=bat.power_plugged,
                seconds_left=bat.secsleft if bat.secsleft not in (-1, -2) else None,
                status=status,
            )
        except Exception:
            return None
