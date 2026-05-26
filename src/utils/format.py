"""Utility functions for formatting hardware values."""


def format_bytes(n: float, suffix: str = "B") -> str:
    for unit in ("", "Ki", "Mi", "Gi", "Ti"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}{suffix}"
        n /= 1024.0
    return f"{n:.1f} Pi{suffix}"


def format_freq_mhz(mhz: float) -> str:
    if mhz >= 1000:
        return f"{mhz / 1000:.2f} GHz"
    return f"{mhz:.0f} MHz"


def format_temp(celsius: float) -> str:
    return f"{celsius:.1f} °C"


def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def format_percent(value: float) -> str:
    return f"{value:.1f} %"


def format_speed(bytes_per_sec: float) -> str:
    return f"{format_bytes(bytes_per_sec)}/s"
