"""Time utilities for conditional access windows.

Centralizes conversions and window checks to keep schemas/services simple.
"""

from __future__ import annotations
from datetime import time
from typing import Optional


def time_to_minutes(t: time) -> int:
    """Convert a datetime.time to minutes since midnight (0..1439)."""
    return t.hour * 60 + t.minute


def minutes_to_hhmm(n: Optional[int]) -> Optional[str]:
    """Format minutes since midnight as HH:MM. Returns None if n is None or invalid."""
    if n is None:
        return None
    try:
        minutes = int(n)
    except Exception:
        return None
    if 0 <= minutes <= 23:
        minutes *= 60
    if not (0 <= minutes <= 1439):
        return None
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


def is_within_window(minute: int, start: int, end: int) -> bool:
    """Return True if minute (0..1439) falls within the window defined by start/end in minutes.

    Semantics:
    - start == end: 24-hour window (always within hours)
    - start < end : standard inclusive range [start..end]
    - start > end : wrap-around window [start..1439] U [0..end]
    """
    if start == end:
        return True
    if start < end:
        return start <= minute <= end
    return minute >= start or minute <= end
