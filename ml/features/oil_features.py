from typing import List, Optional, Union
import numpy as np
import pandas as pd


def clean_oil_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw EIA oil price time series.

    - Standardizes date column to datetime64[ns]
    - Converts values to float, dropping non-positive prices
    - Removes duplicate entries per (period, series)
    - Sorts chronologically ascending
    """
    if df.empty:
        return pd.DataFrame(columns=["period", "series", "value", "source"])

    cleaned = df.copy()

    # Standardize period column
    if "period" not in cleaned.columns:
        raise ValueError("DataFrame missing required 'period' column")
    cleaned["period"] = pd.to_datetime(cleaned["period"], errors="coerce")
    cleaned = cleaned.dropna(subset=["period"])

    # Ensure value column is numeric and valid
    if "value" not in cleaned.columns:
        raise ValueError("DataFrame missing required 'value' column")
    cleaned["value"] = pd.to_numeric(cleaned["value"], errors="coerce")
    cleaned = cleaned.dropna(subset=["value"])
    cleaned = cleaned[cleaned["value"] > 0]

    # Standardize series identifier
    if "series" not in cleaned.columns:
        cleaned["series"] = "OIL_SERIES"

    # Deduplicate and sort chronologically
    cleaned = cleaned.drop_duplicates(subset=["period", "series"], keep="last")
    cleaned = cleaned.sort_values(by=["series", "period"]).reset_index(drop=True)

    return cleaned


def compute_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI) using trailing price changes.
    Uses strictly past information to avoid data leakage.
    """
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's exponential smoothing
    avg_gain = gain.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def build_oil_features(
    df: pd.DataFrame,
    lags: Optional[List[int]] = None,
    rolling_windows: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Constructs time-series features for crude oil price forecasting.

    Engineered feature families:
    1. Returns: 1-day, 5-day, 20-day percentage & log returns
    2. Lags: Past price levels and returns at specified horizons
    3. Rolling Statistics: Trailing moving averages, rolling volatility (annualized)
    4. Momentum & Oscillators: Price-to-MA divergence, MACD (12, 26, 9), RSI (14)

    Anti-leakage guarantee:
    All features utilize strictly trailing data (shift >= 0, rolling without lookahead).
    """
    cleaned = clean_oil_price_data(df)
    if cleaned.empty:
        return cleaned

    if lags is None:
        lags = [1, 2, 3, 5, 10, 20]
    if rolling_windows is None:
        rolling_windows = [7, 14, 30, 90]

    feature_dfs = []

    for series_name, group in cleaned.groupby("series"):
        grp = group.sort_values("period").copy()
        price = grp["value"]

        # 1. Percentage & Log Returns (backward-looking)
        grp["return_1d"] = price.pct_change(1)
        grp["return_5d"] = price.pct_change(5)
        grp["return_20d"] = price.pct_change(20)
        grp["log_return_1d"] = np.log(price / price.shift(1))

        # 2. Lag Features
        for lag in lags:
            grp[f"lag_price_{lag}"] = price.shift(lag)
            grp[f"lag_return_{lag}"] = grp["return_1d"].shift(lag)

        # 3. Trailing Rolling Statistics
        for window in rolling_windows:
            # Trailing rolling mean
            roll_mean = price.rolling(window=window, min_periods=max(2, window // 2)).mean()
            grp[f"rolling_mean_{window}d"] = roll_mean

            # Distance to moving average
            grp[f"price_to_ma_{window}d"] = (price / roll_mean) - 1.0

            # Trailing rolling volatility (annualized based on 252 trading days)
            roll_std = grp["return_1d"].rolling(window=window, min_periods=max(2, window // 2)).std()
            grp[f"rolling_volatility_{window}d"] = roll_std * np.sqrt(252)

        # 4. Momentum & Technical Indicators
        # MACD (12-day EMA - 26-day EMA, 9-day signal)
        ema_12 = price.ewm(span=12, adjust=False).mean()
        ema_26 = price.ewm(span=26, adjust=False).mean()
        grp["macd_line"] = ema_12 - ema_26
        grp["macd_signal"] = grp["macd_line"].ewm(span=9, adjust=False).mean()
        grp["macd_hist"] = grp["macd_line"] - grp["macd_signal"]

        # RSI (14 periods)
        grp["rsi_14"] = compute_rsi(price, window=14)

        # Rolling 30d high-low range normalized position
        roll_min_30 = price.rolling(window=30, min_periods=5).min()
        roll_max_30 = price.rolling(window=30, min_periods=5).max()
        grp["price_range_position_30d"] = (price - roll_min_30) / (roll_max_30 - roll_min_30 + 1e-8)

        feature_dfs.append(grp)

    result = pd.concat(feature_dfs, ignore_index=True)
    return result.sort_values(by=["series", "period"]).reset_index(drop=True)
