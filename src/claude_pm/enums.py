from __future__ import annotations

from enum import Enum


class ProviderType(str, Enum):
    LINEAR = "linear"
    CLICKUP = "clickup"
