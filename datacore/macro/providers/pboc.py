"""央行宏观数据源 — 宏观数据 P1。"""
from __future__ import annotations
from typing import Optional
import httpx
from datacore.macro.providers.base import MacroDataSource
from datacore.macro.models import MacroData, MacroIndicator

PBOC_INDICATORS = {
    "lpr": {"name": "贷款市场报价利率", "url": "https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/3876551/index.html"},
    "m2": {"name": "货币供应量", "url": "https://www.pbc.gov.cn/diaochatongjisi/116219/index.html"},
}


class PboCProvider(MacroDataSource):
    """央行宏观数据。"""
    name = "pboc"
    priority = 1  # P1: 次于统计局

    def fetch_macro(self, indicator: Optional[str] = None,
                    limit: int = 50) -> Optional[MacroData]:
        """从央行获取宏观数据。
        
        使用 pbc.gov.cn 公开数据。
        参数:
            indicator: "lpr", "m2" 之一
            limit: 返回条数
        """
        try:
            ind_key = (indicator or "lpr").lower()
            if ind_key not in PBOC_INDICATORS:
                ind_key = "lpr"
            with httpx.Client(timeout=10, follow_redirects=True) as c:
                resp = c.get(
                    PBOC_INDICATORS[ind_key]["url"],
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                )
                text = resp.text
        except Exception:
            return None
        if not text:
            return None
        # 简单解析：从 HTML 中提取日期和数值
        import re
        date_pattern = r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})?[日]?'
        value_pattern = r'(\d+\.?\d*)\s*[%％]'
        dates = re.findall(date_pattern, text)
        values = re.findall(value_pattern, text)
        indicators = []
        for i in range(min(len(dates), len(values), limit)):
            try:
                date_str = f"{dates[i][0]}-{dates[i][1]}" if dates[i][2] else dates[i][0]
                indicators.append(MacroIndicator(
                    indicator=ind_key,
                    period=date_str,
                    value=float(values[i]),
                    source="pboc",
                    unit="%",
                ))
            except (TypeError, ValueError):
                continue
        if not indicators:
            return None
        return MacroData(indicator=ind_key, total=len(indicators), data=indicators)

    def check_available(self) -> bool:
        try:
            with httpx.Client(timeout=5) as c:
                r = c.head("https://www.pbc.gov.cn")
                return r.status_code < 500
        except Exception:
            return False
