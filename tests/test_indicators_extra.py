"""indicators 模块补充测试。

重点覆盖边界分支、数据不足场景以及未在 test_indicators.py 中完整覆盖的函数。
"""

from __future__ import annotations

import importlib.util
import sys
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from datacore.indicators import compute_indicators
from datacore.indicators.core import (
    INDICATOR_MAP,
    _nan_to_num,
    _rolling_window,
    _shift,
    adx,
    atr,
    bbands,
    bias,
    boll,
    brar,
    cci,
    chandelier,
    cr,
    dmi,
    ema,
    kdj,
    linear_reg_slope,
    linear_regression,
    ma,
    momentum,
    mtm,
    obv,
    psy,
    rate_of_change,
    roc,
    rsi,
    sma,
    stddev,
    stoch,
    trix,
    tsf,
    ultimate_osc,
    variance,
    vr,
    wma,
    wr,
    williams_r,
    get_indicator_names,
)
from datacore.indicators.tdx_compat import (
    _tdx_simple_ma,
    get_tdx_indicator_names,
    tdx_atr,
    tdx_boll,
    tdx_cci,
    tdx_dmi,
    tdx_kdj,
    tdx_ma,
    tdx_obv,
    tdx_rsi,
    tdx_wr,
)
from datacore.indicators.legacy_numpy import (
    get_legacy_function_names,
    old_atr,
    old_boll,
    old_ema,
    old_kdj,
    old_ma,
    old_rsi,
)
from datacore.indicators.trend_maturity import (
    assess_trend_maturity,
    _assess_strength,
    _assess_momentum,
    _assess_volatility,
    _assess_volume,
    _assess_position,
)
from datacore.indicators import talib_wrapper


def _make_close(n: int = 60, seed: int = 7) -> np.ndarray:
    """生成随机收盘价序列。"""
    np.random.seed(seed)
    return 100.0 * np.cumprod(1.0 + np.random.randn(n) * 0.02)


def _make_ohlc(n: int = 60, seed: int = 7) -> dict:
    """生成 OHLCV 测试数据。"""
    np.random.seed(seed)
    close = 100.0 * np.cumprod(1.0 + np.random.randn(n) * 0.02)
    high = close * (1.0 + np.abs(np.random.randn(n)) * 0.01)
    low = close * (1.0 - np.abs(np.random.randn(n)) * 0.01)
    open_ = close * (1.0 + np.random.randn(n) * 0.005)
    volume = np.random.randint(1000, 10000, n).astype(float)
    return {
        "close": close,
        "high": high,
        "low": low,
        "open": open_,
        "volume": volume,
    }


# ============================================================
#  TDX 兼容补充测试
# ============================================================

class TestTdxCompatExtra:
    """TDX 兼容实现补充测试。"""

    def test_tdx_simple_ma_known_values(self):
        """_tdx_simple_ma 已知值验证。"""
        close = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = _tdx_simple_ma(close, 3)
        assert np.isnan(result[0]) and np.isnan(result[1])
        assert pytest.approx(result[2]) == 2.0
        assert pytest.approx(result[3]) == 3.0
        assert pytest.approx(result[4]) == 4.0

    def test_tdx_simple_ma_empty(self):
        """_tdx_simple_ma 空数组输入。"""
        result = _tdx_simple_ma(np.array([]), 3)
        assert len(result) == 0

    def test_tdx_ma_boundary(self):
        """tdx_ma 周期非法或数据不足时返回全 NaN。"""
        close = np.array([1.0, 2.0, 3.0])
        assert np.all(np.isnan(tdx_ma(close, period=0)))
        assert np.all(np.isnan(tdx_ma(close, period=5)))

    def test_tdx_ma_invalid_type_fallback(self):
        """tdx_ma 非法 ma_type 回退到简单移动平均。"""
        close = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = tdx_ma(close, period=3, ma_type=99)
        assert pytest.approx(result[2]) == 2.0

    def test_tdx_boll_basic(self):
        """tdx_boll 完整计算。"""
        data = _make_ohlc(60)
        result = tdx_boll(data["close"], period=20, width=2.0)
        assert set(result.keys()) == {"upper", "middle", "lower"}
        for v in result.values():
            assert len(v) == len(data["close"])
        valid = ~np.isnan(result["upper"])
        assert np.all(result["upper"][valid] >= result["middle"][valid])
        assert np.all(result["middle"][valid] >= result["lower"][valid])

    def test_tdx_boll_zero_width(self):
        """tdx_boll width 为 0 时上中下轨相等。"""
        close = _make_close(30)
        result = tdx_boll(close, period=10, width=0.0)
        valid = ~np.isnan(result["middle"])
        np.testing.assert_allclose(
            result["upper"][valid], result["middle"][valid]
        )
        np.testing.assert_allclose(
            result["lower"][valid], result["middle"][valid]
        )

    def test_tdx_boll_insufficient_data(self):
        """tdx_boll 数据不足时返回全 NaN。"""
        close = np.array([1.0, 2.0, 3.0])
        result = tdx_boll(close, period=5)
        for v in result.values():
            assert np.all(np.isnan(v))

    def test_tdx_dmi_basic(self):
        """tdx_dmi 完整计算并返回预期字段。"""
        data = _make_ohlc(100)
        result = tdx_dmi(data["high"], data["low"], data["close"], period=14)
        assert set(result.keys()) == {"pdi", "mdi", "adx", "adxr"}
        for v in result.values():
            assert len(v) == len(data["close"])

    def test_tdx_dmi_insufficient_data(self):
        """tdx_dmi 数据不足时返回全 NaN。"""
        data = _make_ohlc(10)
        result = tdx_dmi(data["high"], data["low"], data["close"], period=14)
        for v in result.values():
            assert np.all(np.isnan(v))

    def test_tdx_obv_basic(self):
        """tdx_obv 完整计算。"""
        close = np.array([1.0, 2.0, 2.0, 1.5, 3.0])
        volume = np.array([100.0, 200.0, 150.0, 120.0, 300.0])
        result = tdx_obv(close, volume)
        assert len(result) == len(close)
        assert result[0] == 0.0
        # 上涨日累加成交量
        assert result[1] == volume[1]
        # 平盘日不变
        assert result[2] == result[1]
        # 下跌日减去成交量
        assert result[3] == result[2] - volume[3]

    def test_tdx_obv_empty(self):
        """tdx_obv 空数组输入。"""
        result = tdx_obv(np.array([]), np.array([]))
        assert len(result) == 0

    def test_tdx_wr_basic(self):
        """tdx_wr 取值范围与极端情况。"""
        data = _make_ohlc(60)
        result = tdx_wr(data["high"], data["low"], data["close"], period=14)
        valid = result[~np.isnan(result)]
        assert np.all((valid >= 0) & (valid <= 100))

    def test_tdx_wr_flat_returns_fifty(self):
        """tdx_wr 在最高价等于最低价时返回 50。"""
        high = np.full(20, 10.0)
        low = np.full(20, 10.0)
        close = np.full(20, 10.0)
        result = tdx_wr(high, low, close, period=14)
        assert np.all(result[13:] == 50.0)

    def test_tdx_wr_insufficient_data(self):
        """tdx_wr 数据不足时返回全 NaN。"""
        data = _make_ohlc(10)
        result = tdx_wr(data["high"], data["low"], data["close"], period=14)
        assert np.all(np.isnan(result))

    def test_tdx_cci_basic(self):
        """tdx_cci 完整计算。"""
        data = _make_ohlc(60)
        result = tdx_cci(data["high"], data["low"], data["close"], period=14)
        assert len(result) == len(data["close"])

    def test_tdx_cci_flat_returns_zero(self):
        """tdx_cci 在 typ 等于均线时返回 0。"""
        high = np.full(20, 10.0)
        low = np.full(20, 10.0)
        close = np.full(20, 10.0)
        result = tdx_cci(high, low, close, period=14)
        assert np.all(result[13:] == 0.0)

    def test_tdx_cci_insufficient_data(self):
        """tdx_cci 数据不足时返回全 NaN。"""
        data = _make_ohlc(10)
        result = tdx_cci(data["high"], data["low"], data["close"], period=14)
        assert np.all(np.isnan(result))

    def test_get_tdx_indicator_names(self):
        """get_tdx_indicator_names 返回排序后的全部 TDX 指标名。"""
        names = get_tdx_indicator_names()
        assert len(names) > 0
        assert names == sorted(names)
        assert "MA" in names
        assert "KDJ" in names

    def test_tdx_ma_ema_and_smoothed(self):
        """tdx_ma 支持 EMA 与平滑移动平均类型。"""
        close = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        ema_result = tdx_ma(close, period=3, ma_type=1)
        smoothed_result = tdx_ma(close, period=3, ma_type=3)
        assert len(ema_result) == len(close)
        assert len(smoothed_result) == len(close)

    def test_tdx_kdj_insufficient_data(self):
        """tdx_kdj 数据不足时返回全 NaN。"""
        data = _make_ohlc(5)
        result = tdx_kdj(data["high"], data["low"], data["close"], n=10)
        for v in result.values():
            assert np.all(np.isnan(v))

    def test_tdx_rsi_insufficient_data(self):
        """tdx_rsi 数据不足时返回全 NaN。"""
        close = _make_close(5)
        result = tdx_rsi(close, period=14)
        assert np.all(np.isnan(result))

    def test_tdx_atr_insufficient_data(self):
        """tdx_atr 数据不足时返回全 NaN。"""
        data = _make_ohlc(5)
        result = tdx_atr(data["high"], data["low"], data["close"], period=14)
        assert np.all(np.isnan(result))


# ============================================================
#  core.py 补充测试
# ============================================================

class TestCoreExtra:
    """core.py 边界与别名补充测试。"""

    def test_shift_zero(self):
        """_shift 偏移 0 时返回副本。"""
        arr = np.array([1.0, 2.0, 3.0])
        result = _shift(arr, 0)
        np.testing.assert_allclose(result, arr)
        assert result is not arr

    def test_shift_negative(self):
        """_shift 支持负偏移（左移）。"""
        arr = np.array([1.0, 2.0, 3.0])
        result = _shift(arr, -1)
        assert np.isnan(result[-1])
        np.testing.assert_allclose(result[:-1], arr[1:])

    def test_shift_empty(self):
        """_shift 空数组输入。"""
        arr = np.array([], dtype=float)
        result = _shift(arr, 1)
        assert len(result) == 0

    def test_rolling_window_invalid(self):
        """_rolling_window 非法窗口返回空数组。"""
        arr = np.array([1.0, 2.0, 3.0])
        assert len(_rolling_window(arr, 0)) == 0
        assert len(_rolling_window(arr, 5)) == 0
        assert len(_rolling_window(arr, -1)) == 0

    def test_rolling_window_valid(self):
        """_rolling_window 正常窗口形状正确。"""
        arr = np.array([1.0, 2.0, 3.0, 4.0])
        windows = _rolling_window(arr, 2)
        assert windows.shape == (3, 2)

    def test_nan_to_num(self):
        """_nan_to_num 将 NaN 替换为指定值。"""
        arr = np.array([1.0, np.nan, 3.0])
        np.testing.assert_allclose(_nan_to_num(arr), np.array([1.0, 0.0, 3.0]))
        np.testing.assert_allclose(
            _nan_to_num(arr, nan=-1.0), np.array([1.0, -1.0, 3.0])
        )

    @pytest.mark.parametrize(
        "func, kwargs, needs_hl, needs_vol, needs_open",
        [
            (ma, {"period": 0}, False, False, False),
            (ema, {"period": 0}, False, False, False),
            (sma, {"period": 0}, False, False, False),
            (wma, {"period": 0}, False, False, False),
            (rsi, {"period": 14}, False, False, False),
            (mtm, {"period": 10}, False, False, False),
            (roc, {"period": 10}, False, False, False),
            (bias, {"period": 10}, False, False, False),
            (trix, {"period": 12}, False, False, False),
            (cci, {"period": 0}, True, False, False),
            (wr, {"period": 20}, True, False, False),
            (psy, {"period": 12}, False, False, False),
            (atr, {"period": 20}, True, False, False),
            (stddev, {"period": 10}, False, False, False),
            (variance, {"period": 10}, False, False, False),
            (linear_regression, {"period": 10}, False, False, False),
            (linear_reg_slope, {"period": 10}, False, False, False),
            (tsf, {"period": 10}, False, False, False),
            (ultimate_osc, {"period3": 30}, True, False, False),
        ],
    )
    def test_indicator_invalid_or_short_returns_nan(
        self, func, kwargs, needs_hl, needs_vol, needs_open
    ):
        """各指标在非法参数或数据不足时返回全 NaN。"""
        n = 5
        close = _make_close(n)
        args = [close]
        if needs_hl:
            data = _make_ohlc(n)
            args = [data["high"], data["low"], data["close"]]
        if needs_vol:
            args.append(np.ones(n))
        if needs_open:
            args.append(np.ones(n))

        result = func(*args, **kwargs)
        if isinstance(result, dict):
            for v in result.values():
                assert np.all(np.isnan(v))
        else:
            assert np.all(np.isnan(result))

    def test_boll_insufficient_data(self):
        """boll 数据不足时返回全 NaN 字典。"""
        close = _make_close(5)
        result = boll(close, period=10)
        assert set(result.keys()) == {"upper", "middle", "lower"}
        for v in result.values():
            assert np.all(np.isnan(v))

    def test_kdj_insufficient_data(self):
        """kdj 数据不足时返回全 NaN 字典。"""
        data = _make_ohlc(5)
        result = kdj(data["high"], data["low"], data["close"], n=10)
        assert set(result.keys()) == {"k", "d", "j"}
        for v in result.values():
            assert np.all(np.isnan(v))

    def test_dmi_insufficient_data(self):
        """dmi 数据不足时返回全 NaN 字典。"""
        data = _make_ohlc(5)
        result = dmi(data["high"], data["low"], data["close"], period=14)
        assert set(result.keys()) == {"plus_di", "minus_di", "adx", "dx"}
        for v in result.values():
            assert np.all(np.isnan(v))

    def test_obv_empty(self):
        """obv 空数组输入。"""
        result = obv(np.array([]), np.array([]))
        assert len(result) == 0

    def test_brar_insufficient_data(self):
        """brar 数据不足时返回全 NaN 字典。"""
        data = _make_ohlc(5)
        result = brar(
            data["high"], data["low"], data["close"], data["open"], period=10
        )
        assert set(result.keys()) == {"br", "ar"}
        for v in result.values():
            assert np.all(np.isnan(v))

    def test_cr_insufficient_data(self):
        """cr 数据不足时返回全 NaN。"""
        data = _make_ohlc(5)
        result = cr(data["high"], data["low"], data["close"], period=10)
        assert np.all(np.isnan(result))

    def test_chandelier_insufficient_data(self):
        """chandelier 数据不足时返回全 NaN 字典。"""
        data = _make_ohlc(5)
        result = chandelier(
            data["high"], data["low"], data["close"], period=10
        )
        assert set(result.keys()) == {"long_exit", "short_exit"}
        for v in result.values():
            assert np.all(np.isnan(v))

    def test_vr_insufficient_data(self):
        """vr 数据不足或周期非法时返回全 NaN。"""
        close = _make_close(5)
        volume = np.ones(5)
        result = vr(close, volume, period=10)
        assert np.all(np.isnan(result))

    def test_aliases(self):
        """别名函数与原始函数结果一致。"""
        data = _make_ohlc(60)
        close = data["close"]

        np.testing.assert_allclose(
            williams_r(data["high"], data["low"], close, period=14),
            wr(data["high"], data["low"], close, period=14),
        )
        np.testing.assert_allclose(
            momentum(close, period=10), mtm(close, period=10)
        )
        np.testing.assert_allclose(
            rate_of_change(close, period=10), roc(close, period=10)
        )
        bb = bbands(close, period=20, nbdev=2.0)
        bo = boll(close, period=20, nbdev=2.0)
        for k in bb:
            np.testing.assert_allclose(bb[k], bo[k])
        st = stoch(data["high"], data["low"], close, 9, 3, 3)
        kd = kdj(data["high"], data["low"], close, 9, 3, 3)
        np.testing.assert_allclose(st["slowk"], kd["k"])
        np.testing.assert_allclose(st["slowd"], kd["d"])
        np.testing.assert_allclose(
            adx(data["high"], data["low"], close, period=14),
            dmi(data["high"], data["low"], close, period=14)["adx"],
        )

    def test_get_indicator_names(self):
        """get_indicator_names 返回排序列表且与 INDICATOR_MAP 一致。"""
        names = get_indicator_names()
        assert names == sorted(names)
        assert set(names) == set(INDICATOR_MAP.keys())


# ============================================================
#  __init__.py 补充测试
# ============================================================

class TestInitExtra:
    """统一入口与路由边界补充测试。"""

    def test_close_not_ndarray_raises_typeerror(self):
        """close 不是 ndarray 时抛出 TypeError。"""
        with pytest.raises(TypeError):
            compute_indicators({"close": [1.0, 2.0, 3.0]}, "MA")

    def test_missing_high_low_returns_no_key(self):
        """缺少 high/low 时多价格指标返回空结果。"""
        close = _make_close(20)
        data = {"close": close}
        for name in ["KDJ", "CCI", "WR", "ATR", "DMI", "MEDIAN_PRICE", "TRANGE"]:
            result = compute_indicators(data, name)
            assert name not in result

    def test_avg_price_missing_open_returns_no_key(self):
        """AVG_PRICE 缺少 open 时返回空结果。"""
        data = _make_ohlc(20)
        del data["open"]
        result = compute_indicators(data, "AVG_PRICE")
        assert "AVG_PRICE" not in result

    def test_obv_missing_volume_returns_no_key(self):
        """OBV 缺少 volume 时返回空结果。"""
        data = {"close": _make_close(20)}
        result = compute_indicators(data, "OBV")
        assert "OBV" not in result

    def test_brar_missing_open_returns_no_key(self):
        """BRAR 缺少 open 时返回空结果。"""
        data = _make_ohlc(20)
        del data["open"]
        result = compute_indicators(data, "BRAR")
        assert "BRAR" not in result

    def test_use_tdx_unhandled_falls_back_to_core(self):
        """use_tdx=True 时未在 TDX 映射中处理的指标回退到 core。"""
        data = _make_ohlc(60)
        result = compute_indicators(data, "EMA", use_tdx=True)
        assert "EMA" in result
        assert len(result["EMA"]) == len(data["close"])

    def test_use_tdx_missing_high_low_returns_no_key(self):
        """use_tdx=True 且缺少 high/low 时 TDX 路由返回 None。"""
        data = {"close": _make_close(20)}
        result = compute_indicators(data, "KDJ", use_tdx=True)
        assert "KDJ" not in result

    def test_use_tdx_kdj_with_high_low(self):
        """use_tdx=True 且 high/low 齐全时走 TDX KDJ 路由。"""
        data = _make_ohlc(60)
        result = compute_indicators(data, "KDJ", use_tdx=True)
        assert "KDJ" in result
        assert set(result["KDJ"].keys()) == {"k", "d", "j"}

    def test_use_tdx_obv_with_volume(self):
        """use_tdx=True 且 volume 齐全时走 TDX OBV 路由。"""
        data = _make_ohlc(60)
        result = compute_indicators(data, "OBV", use_tdx=True)
        assert "OBV" in result
        assert len(result["OBV"]) == len(data["close"])

    def test_use_tdx_obv_missing_volume_returns_no_key(self):
        """use_tdx=True 且缺少 volume 时 TDX OBV 路由返回 None。"""
        data = {"close": _make_close(20)}
        result = compute_indicators(data, "OBV", use_tdx=True)
        assert "OBV" not in result

    def test_cr_missing_high_low_returns_no_key(self):
        """CR 缺少 high/low 时返回空结果。"""
        data = {"close": _make_close(20)}
        result = compute_indicators(data, "CR")
        assert "CR" not in result

    def test_talib_fallback_success(self, monkeypatch):
        """TA-Lib 兜底成功时返回其结果。"""
        dummy = np.array([1.0, 2.0, 3.0])
        monkeypatch.setattr(
            "datacore.indicators.talib_wrapper.compute_with_talib",
            lambda *args, **kwargs: dummy,
        )
        result = compute_indicators({"close": dummy}, "KDJ")
        assert "KDJ" in result
        np.testing.assert_allclose(result["KDJ"], dummy)

    def test_talib_fallback_exception_swallowed(self, monkeypatch):
        """TA-Lib 兜底抛出异常时被吞掉并返回空结果。"""
        def _raise(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(
            "datacore.indicators.talib_wrapper.compute_with_talib", _raise
        )
        data = {"close": _make_close(20)}
        result = compute_indicators(data, "KDJ")
        assert "KDJ" not in result


# ============================================================
#  legacy_numpy.py 补充测试
# ============================================================

class TestLegacyExtra:
    """旧版兼容实现补充测试。"""

    def test_old_ma_insufficient_data(self):
        """old_ma 周期非法或数据不足时返回全 NaN。"""
        close = np.array([1.0, 2.0, 3.0])
        assert np.all(np.isnan(old_ma(close, 0)))
        assert np.all(np.isnan(old_ma(close, 5)))

    def test_old_ema_empty(self):
        """old_ema 空数组输入。"""
        result = old_ema(np.array([]), 12)
        assert len(result) == 0

    def test_old_rsi_insufficient_data(self):
        """old_rsi 数据不足时返回全 NaN。"""
        close = np.array([1.0, 2.0, 3.0])
        assert np.all(np.isnan(old_rsi(close, 14)))

    def test_old_kdj_insufficient_data(self):
        """old_kdj 数据不足时返回全 NaN 元组。"""
        data = _make_ohlc(5)
        k, d, j = old_kdj(
            data["high"], data["low"], data["close"], n=10
        )
        assert np.all(np.isnan(k))
        assert np.all(np.isnan(d))
        assert np.all(np.isnan(j))

    def test_old_boll_insufficient_data(self):
        """old_boll 数据不足时返回全 NaN 元组。"""
        close = np.array([1.0, 2.0, 3.0])
        upper, mid, lower = old_boll(close, n=5)
        assert np.all(np.isnan(upper))
        assert np.all(np.isnan(mid))
        assert np.all(np.isnan(lower))

    def test_old_atr_basic(self):
        """old_atr 基本计算。"""
        data = _make_ohlc(60)
        result = old_atr(data["high"], data["low"], data["close"], n=14)
        assert len(result) == len(data["close"])
        valid = result[~np.isnan(result)]
        assert np.all(valid >= 0)

    def test_old_atr_insufficient_data(self):
        """old_atr 周期非法或数据不足时返回全 NaN。"""
        data = _make_ohlc(5)
        result = old_atr(data["high"], data["low"], data["close"], n=14)
        assert np.all(np.isnan(result))
        result2 = old_atr(data["close"], data["close"], data["close"], n=0)
        assert np.all(np.isnan(result2))

    def test_get_legacy_function_names(self):
        """get_legacy_function_names 返回排序后的旧版函数名。"""
        names = get_legacy_function_names()
        assert len(names) > 0
        assert names == sorted(names)
        assert "old_ma" in names


# ============================================================
#  talib_wrapper.py mock 测试
# ============================================================

class TestTALibWrapper:
    """TA-Lib 封装模块 mock 测试。"""

    def setup_method(self):
        """每个用例前重置 TA-Lib 可用性缓存。"""
        talib_wrapper._talib_available = None

    def teardown_method(self):
        """每个用例后清理 TA-Lib 可用性缓存。"""
        talib_wrapper._talib_available = None

    # --- helper fixtures -------------------------------------------------

    def _fake_talib(self):
        """构造一个包含所有必需函数的 mock talib 模块。"""
        fake = MagicMock()
        fake.MA.return_value = np.array([1.0, 2.0, 3.0])
        fake.EMA.return_value = np.array([1.0, 2.0, 3.0])
        fake.RSI.return_value = np.array([1.0, 2.0, 3.0])
        fake.MACD.return_value = (
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
        )
        fake.BBANDS.return_value = (
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
        )
        fake.ATR.return_value = np.array([1.0, 2.0, 3.0])
        fake.STOCH.return_value = (
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
        )
        fake.CCI.return_value = np.array([1.0, 2.0, 3.0])
        fake.WILLR.return_value = np.array([1.0, 2.0, 3.0])
        fake.ADX.return_value = np.array([1.0, 2.0, 3.0])
        fake.PLUS_DI.return_value = np.array([1.0, 2.0, 3.0])
        fake.MINUS_DI.return_value = np.array([1.0, 2.0, 3.0])
        fake.DX.return_value = np.array([1.0, 2.0, 3.0])
        fake.OBV.return_value = np.array([1.0, 2.0, 3.0])
        fake.MOM.return_value = np.array([1.0, 2.0, 3.0])
        fake.ROC.return_value = np.array([1.0, 2.0, 3.0])
        fake.TRANGE.return_value = np.array([1.0, 2.0, 3.0])
        fake.STDDEV.return_value = np.array([1.0, 2.0, 3.0])
        fake.LINEARREG.return_value = np.array([1.0, 2.0, 3.0])
        fake.LINEARREG_SLOPE.return_value = np.array([1.0, 2.0, 3.0])
        fake.TSF.return_value = np.array([1.0, 2.0, 3.0])
        fake.ULTOSC.return_value = np.array([1.0, 2.0, 3.0])
        fake.MASS.return_value = np.array([1.0, 2.0, 3.0])
        return fake

    def _call_wrapper(self, name, func, data):
        """根据指标名称调用对应的 wrapper 函数。"""
        if name == "MA":
            return func(data["close"], period=5, matype=0)
        if name in [
            "EMA", "RSI", "MTM", "ROC", "STDDEV",
            "LINEARREG", "LINEARREG_SLOPE", "TSF",
        ]:
            return func(data["close"])
        if name in ["MACD", "BOLL"]:
            return func(data["close"])
        if name in [
            "ATR", "CCI", "WR", "ADX", "DMI", "KDJ",
            "TRANGE", "ULTOSC", "MASS",
        ]:
            if name == "MASS":
                return func(data["high"], data["low"])
            return func(data["high"], data["low"], data["close"])
        if name == "OBV":
            return func(data["close"], data["volume"])
        raise ValueError(f"unknown wrapper {name}")

    def _talib_func_name(self, name):
        """返回 wrapper 内部实际调用的 talib 函数名。"""
        mapping = {
            "MA": "MA",
            "EMA": "EMA",
            "RSI": "RSI",
            "MACD": "MACD",
            "BOLL": "BBANDS",
            "ATR": "ATR",
            "KDJ": "STOCH",
            "CCI": "CCI",
            "WR": "WILLR",
            "ADX": "ADX",
            "DMI": "PLUS_DI",
            "OBV": "OBV",
            "MTM": "MOM",
            "ROC": "ROC",
            "TRANGE": "TRANGE",
            "STDDEV": "STDDEV",
            "LINEARREG": "LINEARREG",
            "LINEARREG_SLOPE": "LINEARREG_SLOPE",
            "TSF": "TSF",
            "ULTOSC": "ULTOSC",
            "MASS": "MASS",
        }
        return mapping[name]

    # --- is_talib_available / _get_talib --------------------------------

    def test_is_talib_available_true(self):
        """TA-Lib 可找到时返回 True。"""
        with patch.object(importlib.util, "find_spec", return_value=Mock()):
            assert talib_wrapper.is_talib_available() is True

    def test_is_talib_available_false(self):
        """TA-Lib 不可找到时返回 False。"""
        with patch.object(importlib.util, "find_spec", return_value=None):
            assert talib_wrapper.is_talib_available() is False

    def test_is_talib_available_cached(self):
        """缓存命中时直接返回，不重复查找。"""
        talib_wrapper._talib_available = True
        with patch.object(importlib.util, "find_spec") as mock_find:
            assert talib_wrapper.is_talib_available() is True
            mock_find.assert_not_called()

        talib_wrapper._talib_available = False
        with patch.object(importlib.util, "find_spec") as mock_find:
            assert talib_wrapper.is_talib_available() is False
            mock_find.assert_not_called()

    def test_get_talib_success(self):
        """TA-Lib 导入成功时返回模块对象。"""
        fake_talib = self._fake_talib()
        with patch.object(importlib.util, "find_spec", return_value=Mock()):
            with patch.dict(sys.modules, {"talib": fake_talib}):
                result = talib_wrapper._get_talib()
                assert result is fake_talib

    def test_get_talib_not_available(self):
        """TA-Lib 不可用时 _get_talib 直接返回 None。"""
        talib_wrapper._talib_available = False
        with patch.object(importlib.util, "find_spec") as mock_find:
            result = talib_wrapper._get_talib()
            assert result is None
            mock_find.assert_not_called()

    def test_get_talib_import_failure(self):
        """TA-Lib 导入失败时返回 None 并标记为不可用。"""
        with patch.object(importlib.util, "find_spec", return_value=Mock()):
            with patch.dict(sys.modules, {"talib": None}):
                result = talib_wrapper._get_talib()
                assert result is None
                assert talib_wrapper._talib_available is False

    # --- wrapper functions ----------------------------------------------

    @pytest.mark.parametrize(
        "name", list(talib_wrapper.TALIB_FUNCTION_MAP.keys())
    )
    def test_wrapper_unavailable_returns_none(self, name):
        """TA-Lib 不可用时每个 wrapper 都返回 None。"""
        data = _make_ohlc(10)
        func = talib_wrapper.TALIB_FUNCTION_MAP[name]
        with patch.object(talib_wrapper, "_get_talib", return_value=None):
            result = self._call_wrapper(name, func, data)
            assert result is None

    @pytest.mark.parametrize(
        "name", list(talib_wrapper.TALIB_FUNCTION_MAP.keys())
    )
    def test_wrapper_success(self, name):
        """TA-Lib 可用时每个 wrapper 都返回预期结果。"""
        data = _make_ohlc(10)
        fake = self._fake_talib()
        func = talib_wrapper.TALIB_FUNCTION_MAP[name]
        with patch.object(talib_wrapper, "_get_talib", return_value=fake):
            result = self._call_wrapper(name, func, data)
            assert result is not None
            if isinstance(result, dict):
                assert len(result) > 0
                for v in result.values():
                    assert isinstance(v, np.ndarray)

    @pytest.mark.parametrize(
        "name", list(talib_wrapper.TALIB_FUNCTION_MAP.keys())
    )
    def test_wrapper_exception_returns_none(self, name):
        """TA-Lib 函数抛出异常时 wrapper 返回 None。"""
        data = _make_ohlc(10)
        fake = self._fake_talib()
        talib_name = self._talib_func_name(name)
        getattr(fake, talib_name).side_effect = RuntimeError("boom")
        func = talib_wrapper.TALIB_FUNCTION_MAP[name]
        with patch.object(talib_wrapper, "_get_talib", return_value=fake):
            result = self._call_wrapper(name, func, data)
            assert result is None

    # --- compute_with_talib ---------------------------------------------

    def test_compute_with_talib_unavailable(self):
        """TA-Lib 不可用时 compute_with_talib 返回 None。"""
        data = _make_ohlc(10)
        with patch.object(
            talib_wrapper, "is_talib_available", return_value=False
        ):
            result = talib_wrapper.compute_with_talib("MA", data)
            assert result is None

    def test_compute_with_talib_unknown_name(self):
        """未知指标名返回 None。"""
        data = _make_ohlc(10)
        with patch.object(
            talib_wrapper, "is_talib_available", return_value=True
        ):
            result = talib_wrapper.compute_with_talib("UNKNOWN", data)
            assert result is None

    @pytest.mark.parametrize(
        "name", list(talib_wrapper.TALIB_FUNCTION_MAP.keys())
    )
    def test_compute_with_talib_routes_success(self, name):
        """compute_with_talib 覆盖所有指标类型路由。"""
        data = _make_ohlc(10)
        fake = self._fake_talib()
        with patch.object(
            talib_wrapper, "is_talib_available", return_value=True
        ):
            with patch.object(
                talib_wrapper, "_get_talib", return_value=fake
            ):
                result = talib_wrapper.compute_with_talib(name, data)
                assert result is not None

    def test_compute_with_talib_else_branch(self):
        """compute_with_talib 的 else 分支返回 None。"""
        data = _make_ohlc(10)
        fake = self._fake_talib()
        original_map = talib_wrapper.TALIB_FUNCTION_MAP.copy()
        try:
            talib_wrapper.TALIB_FUNCTION_MAP["ZZZ"] = (
                lambda *a, **k: None
            )
            with patch.object(
                talib_wrapper, "is_talib_available", return_value=True
            ):
                with patch.object(
                    talib_wrapper, "_get_talib", return_value=fake
                ):
                    result = talib_wrapper.compute_with_talib("ZZZ", data)
                    assert result is None
        finally:
            talib_wrapper.TALIB_FUNCTION_MAP = original_map

    def test_compute_with_talib_exception(self):
        """compute_with_talib 内部异常时返回 None。"""
        data = _make_ohlc(10)
        original_func = talib_wrapper.TALIB_FUNCTION_MAP["MA"]
        try:
            talib_wrapper.TALIB_FUNCTION_MAP["MA"] = (
                lambda *a, **k: (_ for _ in ()).throw(
                    RuntimeError("boom")
                )
            )
            with patch.object(
                talib_wrapper, "is_talib_available", return_value=True
            ):
                result = talib_wrapper.compute_with_talib("MA", data)
                assert result is None
        finally:
            talib_wrapper.TALIB_FUNCTION_MAP["MA"] = original_func

    # --- list_talib_indicators ------------------------------------------

    def test_get_talib_indicator_names(self):
        """get_talib_indicator_names 返回排序后的指标名列表。"""
        names = talib_wrapper.get_talib_indicator_names()
        assert names == sorted(names)
        assert set(names) == set(talib_wrapper.TALIB_FUNCTION_MAP.keys())


# ============================================================
#  trend_maturity.py 边界覆盖
# ============================================================

class TestTrendMaturityExtra:
    """趋势成熟度评估边界分支补充测试。"""

    def _make_flat_ohlc(self, n: int = 60) -> dict:
        """生成近似横盘、低波动的 OHLCV 数据。"""
        t = np.arange(n)
        close = 100.0 + 1.5 * np.sin(t * 0.25)
        high = close + np.where(t < 40, 0.8, 0.05)
        low = close - np.where(t < 40, 0.8, 0.05)
        volume = np.where(t < 40, 1000.0, 300.0)
        return {"close": close, "high": high, "low": low, "volume": volume}

    def test_assess_trend_maturity_sideways_direction(self):
        """横盘数据应识别为 sideways 方向。"""
        data = self._make_flat_ohlc(80)
        result = assess_trend_maturity(
            data["close"], data["high"], data["low"], data["volume"]
        )
        assert result.trend_direction == "sideways"

    def test_assess_trend_maturity_early_stage(self, monkeypatch):
        """低分数据应识别为 early 阶段。"""
        close = np.full(60, 100.0)
        monkeypatch.setattr(
            "datacore.indicators.trend_maturity._assess_strength",
            lambda *a, **k: (20.0, {}),
        )
        monkeypatch.setattr(
            "datacore.indicators.trend_maturity._assess_momentum",
            lambda *a, **k: (20.0, {}),
        )
        monkeypatch.setattr(
            "datacore.indicators.trend_maturity._assess_volatility",
            lambda *a, **k: (20.0, {}),
        )
        monkeypatch.setattr(
            "datacore.indicators.trend_maturity._assess_volume",
            lambda *a, **k: (20.0, {}),
        )
        monkeypatch.setattr(
            "datacore.indicators.trend_maturity._assess_position",
            lambda *a, **k: (20.0, {}),
        )
        result = assess_trend_maturity(close)
        assert result.stage == "early"
        assert result.score < 30

    def test_assess_strength_ma_converging(self):
        """短期与长期均线同向且短斜率不超过长斜率。"""
        # 前 30 根快速上涨，后 30 根缓慢上涨 -> 短斜率 <= 长斜率
        close = np.concatenate([
            np.linspace(100.0, 130.0, 30),
            np.linspace(130.0, 135.0, 30),
        ])
        high = close + 0.6
        low = close - 0.6
        score, feats = _assess_strength(close, high, low)
        assert feats.get("ma_divergence") == "converging"
        assert feats["short_ma_slope"] > 0
        assert feats["long_ma_slope"] > 0

    def test_assess_momentum_macd_declining_high_ratio(self):
        """MACD 柱体大且下降。"""
        # 前期上涨后接平方加速下跌，可产生负向且持续放大的 MACD 柱体
        close = np.concatenate([
            np.linspace(100.0, 140.0, 30),
            140.0 - np.linspace(0.0, 1.0, 30) ** 2 * 80.0,
        ])
        score, feats = _assess_momentum(close)
        assert "macd_hist_slope" in feats
        assert feats["macd_hist_slope"] < 0
        assert feats["macd_hist_ratio"] > 0.5

    def test_assess_volatility_high_atr_ratio(self):
        """ATR 变化率 > 2.0。"""
        close = np.full(60, 100.0)
        high = close + 0.5
        low = close - 0.5
        high[-5:] += 8.0
        low[-5:] -= 8.0
        score, feats = _assess_volatility(close, high, low)
        assert "atr_change" in feats
        assert feats["atr_change"] > 2.0

    def test_assess_volatility_moderate_atr_ratio(self):
        """ATR 变化率 > 1.5。"""
        close = np.full(60, 100.0)
        high = close + 0.5
        low = close - 0.5
        high[-5:] += 1.8
        low[-5:] -= 1.8
        score, feats = _assess_volatility(close, high, low)
        assert 1.5 < feats["atr_change"] < 2.0

    def test_assess_volatility_low_atr_ratio(self):
        """ATR 变化率 < 0.7。"""
        close = np.full(60, 100.0)
        # 前 40 根波动较大，后 20 根波动急剧收缩
        high = np.concatenate([close[:40] + 0.3, close[40:] + 0.01])
        low = np.concatenate([close[:40] - 0.3, close[40:] - 0.01])
        score, feats = _assess_volatility(close, high, low)
        assert "atr_change" in feats
        assert feats["atr_change"] < 0.7

    def test_assess_volatility_high_bandwidth_ratio(self):
        """布林带带宽比 > 1.8。"""
        # 前 55 根低波动，后 5 根高波动，使当前带宽显著高于近期均值
        historical = 100.0 + np.random.default_rng(7).normal(0.0, 0.2, 55)
        recent = 100.0 + np.random.default_rng(8).normal(0.0, 8.0, 5)
        close = np.concatenate([historical, recent])
        high = close + 0.5
        low = close - 0.5
        score, feats = _assess_volatility(close, high, low)
        assert "bw_ratio" in feats
        assert feats["bw_ratio"] > 1.8

    def test_assess_volatility_low_bandwidth_ratio(self):
        """布林带带宽比 < 0.6。"""
        np.random.seed(8)
        historical = 100.0 + np.random.randn(40) * 5.0
        recent = 100.0 + np.random.randn(20) * 0.2
        close = np.concatenate([historical, recent])
        high = close + 0.5
        low = close - 0.5
        score, feats = _assess_volatility(close, high, low)
        assert "bw_ratio" in feats
        assert feats["bw_ratio"] < 0.6

    def test_assess_volume_bearish_obv_divergence(self):
        """价格上涨但 OBV 下降 -> 顶背离。"""
        close = np.full(60, 100.0)
        volume = np.full(60, 1000.0)
        # 最后 20 根：收盘价整体上涨，但下跌日配大成交量，使 OBV 在最后 10 根持续下降
        close[-20:] = [
            100, 102, 101, 103, 102, 104, 103, 105, 104, 106,
            105, 107, 106, 108, 107, 109, 108, 110, 109, 111,
        ]
        volume[-20:] = [
            1000, 1000, 50000, 1000, 50000, 1000, 50000, 1000, 50000, 1000,
            50000, 1000, 50000, 1000, 50000, 1000, 50000, 1000, 50000, 1000,
        ]
        score, feats = _assess_volume(close, volume)
        assert feats.get("obv_divergence") == "bearish"

    def test_assess_volume_bullish_obv_divergence(self):
        """价格下跌但 OBV 上升 -> 底背离。"""
        close = np.full(60, 100.0)
        volume = np.full(60, 1000.0)
        # 最后 20 根：收盘价整体下跌，但上涨日配大成交量，使 OBV 在最后 10 根持续上升
        close[-20:] = [
            100, 98, 99, 97, 98, 96, 97, 95, 96, 94,
            95, 93, 94, 92, 93, 91, 92, 90, 91, 89,
        ]
        volume[-20:] = [
            1000, 1000, 50000, 1000, 50000, 1000, 50000, 1000, 50000, 1000,
            50000, 1000, 50000, 1000, 50000, 1000, 50000, 1000, 50000, 1000,
        ]
        score, feats = _assess_volume(close, volume)
        assert feats.get("obv_divergence") == "bullish"

    def test_assess_volume_high_volume_ratio(self):
        """成交量比 > 2.0。"""
        close = np.full(60, 100.0)
        volume = np.full(60, 1000.0)
        volume[-10:] = 3000.0
        score, feats = _assess_volume(close, volume)
        assert feats["volume_ratio"] > 2.0

    def test_assess_volume_low_volume_ratio(self):
        """成交量比 < 0.5。"""
        close = np.full(60, 100.0)
        volume = np.full(60, 1000.0)
        volume[-10:] = 200.0
        score, feats = _assess_volume(close, volume)
        assert feats["volume_ratio"] < 0.5

    def test_assess_position_middle(self):
        """价格位于周期中部 -> score=40。"""
        close = np.concatenate([
            np.linspace(90.0, 110.0, 40),
            np.full(20, 100.0),
        ])
        score, feats = _assess_position(close)
        assert 20 < feats["price_position"] < 80
        assert score == 40.0
