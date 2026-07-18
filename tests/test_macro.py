import pytest
from datacore.macro.models import MacroIndicator, MacroData


class TestMacroModels:
    def test_macro_indicator(self):
        mi = MacroIndicator(
            indicator="pmi",
            period="2026-06",
            value=50.5,
            prev_value=49.8,
            yoy=1.4,
            source="eastmoney",
            unit="%",
        )
        assert mi.indicator == "pmi"
        assert mi.value == 50.5

    def test_macro_data_latest(self):
        md = MacroData(indicator="pmi", data=[
            MacroIndicator(indicator="pmi", period="2026-06", value=50.5),
            MacroIndicator(indicator="pmi", period="2026-05", value=49.8),
        ])
        latest = md.latest()
        assert latest is not None
        assert latest.value == 50.5

    def test_macro_data_empty(self):
        md = MacroData()
        assert md.latest() is None
        assert md.total == 0
