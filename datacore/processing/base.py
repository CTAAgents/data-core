"""数据加工阶段抽象基类。

所有数据加工阶段（情绪打分、市场制度检测等）继承此基类，
统一接口契约，支持降级链编排。
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional


class ProcessingStage(ABC):
    """数据加工阶段抽象基类。

    每个加工阶段有明确的输入/输出类型声明，
    支持降级链编排（如 LLM 打分失败时降级到规则基线）。

    Attributes:
        input_type: 输入数据类型声明（如 "NEWS"）
        output_type: 输出数据类型声明（如 "SENTIMENT_ITEM"）
        name: 阶段名称，用于日志和降级链标识
        priority: 优先级（0=最高），用于降级链排序
    """

    input_type: str = ""
    output_type: str = ""
    name: str = ""
    priority: int = 0

    @abstractmethod
    def process(self, input_data: Any, symbol: Optional[str] = None,
                params: Optional[dict] = None) -> Any:
        """执行数据加工。

        Args:
            input_data: 输入数据（类型由 input_type 声明）
            symbol: 品种代码（如 "RB"），None 表示全市场
            params: 加工参数

        Returns:
            加工后的数据（类型由 output_type 声明）
        """
        raise NotImplementedError

    def check_available(self) -> bool:
        """检查此加工阶段是否可用（如 LLM 依赖是否安装）。"""
        return True
