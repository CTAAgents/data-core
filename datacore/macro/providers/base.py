"""宏观数据源基类。"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from datacore.macro.models import MacroData


class MacroDataSource(ABC):
    name: str = ""
    priority: int = 99

    @abstractmethod
    def fetch_macro(self, indicator: Optional[str] = None,
                    limit: int = 50) -> Optional[MacroData]:
        """获取宏观数据。"""

    def check_available(self) -> bool:
        return True
