# 0) 사전: 필요한 라이브러리 설치/임포트
# pip install pyarrow yfinance quantstats

import os
import json
import time
from datetime import datetime

import numpy as np
import pandas as pd

import yfinance as yf
import quantstats as qs

# -----------------
# 경로 설정
# -----------------
universe_path = r"C:\MultiFactor_Project\backtest_universe_3000.json"
parquet_path = r"C:\MultiFactor_Project\DataBase\backtest_data_2026_02_03.parquet"

print("universe ok?", os.path.exists(universe_path))
import pyarrow.parquet as pq

import matplotlib.pyplot as plt
plt.style.use("dark_background")

# -----------------------------------------------------------------------------
# 1) 데이터 준비 함수: parquet에서 로드 + 인덱스 정리
# -----------------------------------------------------------------------------
def prepare_backtest_data(
    top_n,
    factors,
    universe_dict=None,
    parquet_filename=r"C:\MultiFactor_Project\DataBase\backtest_data_2026_02_03.parquet",
    universe_json=r"C:\MultiFactor_Project\backtest_universe_3000.json",
):
    if universe_dict is None:
        with open(universe_json, "r", encoding="utf-8") as f:
            universe_dict = json.load(f)

    if not os.path.exists(parquet_filename):
        raise FileNotFoundError(f"parquet 파일이 없습니다: {parquet_filename}")

    target_tickers = set()
    for _, tickers in universe_dict.items():
        target_tickers.update(tickers[:top_n])
    target_list = sorted(target_tickers)

    base_cols = ["date", "sector", "open", "close", "volume", "symbol"]
    fcols = list(factors)
    req_cols = list(dict.fromkeys(base_cols + fcols))

    tbl = pq.read_table(
        parquet_filename,
        columns=req_cols,
        filters=[("symbol", "in", target_list)],
    )
    df = tbl.to_pandas()
    del tbl

    df["date"] = pd.to_datetime(df["date"])
    if "sector" in df.columns:
        df["sector"] = df["sector"].astype("object")
    for c in fcols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(np.float32)

    df = df.sort_values(["symbol", "date"])
    if "sector" in df.columns:
        df["sector"] = (
            df["sector"]
            .replace(["", "Unknown"], np.nan)
            .groupby(df["symbol"])
            .ffill()
            .fillna("Unknown")
        )
    for c in fcols:
        if c in df.columns:
            df[c] = df.groupby("symbol")[c].ffill()

    df = df.sort_values(["date", "symbol"])
    df_final = df.set_index(["date", "symbol"]).sort_index()
    return df_final

# -----------------------------------------------------------------------------
# 2) 이상치/결측 패널 정리 함수
# -----------------------------------------------------------------------------
def clean_factor_panel(df_factor, verbose=True):
    if "open" not in df_factor.columns or "close" not in df_factor.columns:
        raise ValueError("df_factor에 'open'/'close' 컬럼이 필요합니다.")

    def compute_flags_for_col(px):
        px = px.replace([np.inf, -np.inf], np.nan)
        nonpos_count = (px <= 0).sum(axis=0)
        px = px.where(px > 0, np.nan)
        miss_ratio = px.isna().mean(axis=0)
        px_ff = px.ffill()
        ret = px_ff.pct_change()
        jump_events = (ret.abs() > 1.0).sum(axis=0)
        flat_days = (px_ff.diff() == 0)
        flat_windows = flat_days.rolling(5).sum()
        flat_events = (flat_windows >= 4).sum(axis=0)
        min_price_flag = (px_ff.min(axis=0) < 1.0)
        drop_flag = (
            (jump_events >= 3)
            | (flat_events >= 3)
            | (nonpos_count > 0)
            | (miss_ratio > 0.2)
            | (min_price_flag)
        )
        return pd.DataFrame({
            "jump_events": jump_events,
            "flat_events": flat_events,
            "nonpos_count": nonpos_count,
            "missing_ratio": miss_ratio,
            "min_price": px_ff.min(axis=0),
            "drop": drop_flag
        }), drop_flag

    open_px = df_factor["open"].unstack("symbol").sort_index()
    close_px = df_factor["close"].unstack("symbol").sort_index()
    report_o, drop_o = compute_flags_for_col(open_px)
    report_c, drop_c = compute_flags_for_col(close_px)
    drop_both = drop_o & drop_c
    keep = set(report_o.index) - set(drop_both[drop_both].index)
    cleaned = df_factor[df_factor.index.get_level_values("symbol").isin(keep)].copy()

    if verbose:
        print("clean_factor_panel: before:", len(report_o), "after:", len(keep))
    return cleaned, pd.concat([
        report_o.add_prefix("open_"),
        report_c.add_prefix("close_"),
        drop_both.rename("drop_both")
    ], axis=1, sort=False)

# -----------------------------------------------------------------------------
# 3) 필터 전략 백테스트 함수
# -----------------------------------------------------------------------------
def filtered_multifactor_test(
    df_data,
    universe_dict,
    top_n,
    filter_conditions,
    name="FilteredMultifactor",
    cost_bps=20.0,
    start_date=None,
    end_date=None,
):
    raw_rebalance_dates = sorted(universe_dict.keys())
    valid_dates_idx = df_data.index.unique(level="date").sort_values()
    full_date_range = valid_dates_idx[valid_dates_idx >= pd.Timestamp(raw_rebalance_dates[0])]

    if start_date is not None:
        full_date_range = full_date_range[full_date_range >= pd.Timestamp(start_date)]
    if end_date is not None:
        full_date_range = full_date_range[full_date_range <= pd.Timestamp(end_date)]
    if full_date_range.empty:
        raise ValueError("기간 내 거래일이 없습니다.")

    aligned_dates_map = {}
    for d_str in raw_rebalance_dates:
        ts = pd.Timestamp(d_str)
        if ts < full_date_range[0] or ts > full_date_range[-1]:
            continue
        closest = valid_dates_idx.asof(ts)
        if pd.notna(closest):
            aligned_dates_map[d_str] = closest
    trading_rebalance_dates = sorted(set(aligned_dates_map.values()))
    inverse_aligned_map = {v:k for k,v in aligned_dates_map.items()}

    # SPY 벤치마크
    results_summary = []
    lines = []
    try:
        spy = yf.Ticker("SPY").history(start=full_date_range[0], end=full_date_range[-1] + pd.Timedelta(days=5))
        spy_series = spy["Close"].tz_localize(None) if spy["Close"].index.tz is not None else spy["Close"]
        spy_series = spy_series.reindex(full_date_range, method="ffill")
        bm_ret = spy_series.pct_change().fillna(0)
        bm_total = (1 + bm_ret).prod() - 1
        bm_cagr = (1 + bm_total) ** (365.25 / ((full_date_range[-1]-full_date_range[0]).days)) - 1
        results_summary.append({
            "Factor": "Benchmark (SPY)",
            "Total Return": f"{bm_total*100:.1f}%",
            "CAGR": f"{bm_cagr*100:.2f}%",
            "Sharpe": f"{qs.stats.sharpe(bm_ret):.2f}",
            "MDD": f"{qs.stats.max_drawdown(bm_ret)*100:.1f}%",
            "Avg Turnover": "0.0%",
        })
        lines.append((None, "Benchmark (SPY)", bm_total))
    except Exception as e:
        print("SPY 로딩 실패:", e)

    # 스크리닝 후 포트폴리오 리밸런싱
    mf_daily_returns = pd.Series(0.0, index=full_date_range)
    mf_prev_weights = pd.Series(dtype=float)
    mf_turnover = []

    for i in range(len(trading_rebalance_dates)-1):
        curr = trading_rebalance_dates[i]
        next_dt = trading_rebalance_dates[i+1]
        if curr < full_date_range[0] or curr >= full_date_range[-1]:
            continue
        curr_pos = full_date_range.get_loc(curr)
        entry = full_date_range[curr_pos + 1]
        try:
            df_curr = df_data.loc[curr]
            key = inverse_aligned_map.get(curr)
            w = pd.Series(dtype=float)
            if key is not None:
                u_list = universe_dict.get(key, [])[:top_n]
                u_df = df_curr.loc[df_curr.index.isin(u_list)].copy()
                mask = pd.Series(True, index=u_df.index)
                for f, (direction, percentile) in filter_conditions.items():
                    if f not in u_df.columns:
                        raise ValueError(f"Factor {f} missing from df_data")
                    s = u_df[f].astype(float)
                    if direction == "upper":
                        thr = s.quantile(1.0 - percentile)
                        mask &= (s >= thr)
                    elif direction == "lower":
                        thr = s.quantile(percentile)
                        mask &= (s <= thr)
                    else:
                        raise ValueError("direction은 'upper' 또는 'lower'")
                candidates = u_df[mask].dropna(subset=list(filter_conditions.keys()))
                if len(candidates) > 0:
                    w = pd.Series(1.0 / len(candidates), index=candidates.index)

            if mf_prev_weights.empty:
                tr = 1.0 if not w.empty else 0.0
            else:
                comb = pd.concat([mf_prev_weights, w], axis=1).fillna(0)
                tr = np.abs(comb.iloc[:,0] - comb.iloc[:,1]).sum() / 2
            mf_turnover.append(tr)
            mf_prev_weights = w

            if not w.empty:
                period = full_date_range[(full_date_range >= entry) & (full_date_range <= next_dt)]
                data_p = df_data.loc[period[0]:period[-1]]
                data_p = data_p[data_p.index.get_level_values("symbol").isin(w.index)]
                px = data_p.pivot_table(index="date", columns="symbol", values="open").ffill()
                ret = px.pct_change().fillna(0)
                wret = (ret * w).sum(axis=1)
                wret.loc[entry] -= tr * (cost_bps / 10000.0)
                mf_daily_returns.loc[wret.index] = wret
        except Exception as e:
            print("리밸런스 에러", curr, e)
            continue

    total = (1 + mf_daily_returns).prod() - 1
    years = (full_date_range[-1] - full_date_range[0]).days / 365.25
    cagr = (1 + total)**(1/years) - 1 if years > 0 else 0
    sharpe = qs.stats.sharpe(mf_daily_returns)
    mdd = qs.stats.max_drawdown(mf_daily_returns)

    results_summary.append({
        "Factor": name,
        "Total Return": f"{total*100:.1f}%",
        "CAGR": f"{cagr*100:.2f}%",
        "Sharpe": f"{sharpe:.2f}",
        "MDD": f"{mdd*100:.1f}%",
        "Avg Turnover": f"{(np.mean(mf_turnover)*100 if mf_turnover else 0):.1f}%",
    })

    nav = (1 + mf_daily_returns).cumprod()
    plt.figure(figsize=(12,6))
    plt.plot(nav.index, nav, linewidth=2.2, label=name)
    plt.title(f"{name} NAV")
    plt.legend()
    plt.show()

    summary_df = pd.DataFrame(results_summary).set_index("Factor")
    print(summary_df)

    return summary_df, mf_daily_returns, {
        "full_date_range": full_date_range,
        "trading_rebalance_dates": trading_rebalance_dates,
        "inverse_aligned_map": inverse_aligned_map,
    }

# -----------------------------------------------------------------------------
# 4) 실행 블록 (실행 시 이 부분만 쓰면 됨)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    universe_path = r"C:\MultiFactor_Project\backtest_universe_3000.json"
    parquet_path = r"C:\MultiFactor_Project\DataBase\backtest_data_2026_02_03.parquet"

    with open(universe_path, "r", encoding="utf-8") as f:
        universe_dict = json.load(f)

    MY_FACTORS = [
        'priceToEarningsRatio',
        'priceToBookRatio',
        'evToEBITDA',
        'returnOnEquity',
        'freeCashFlow',
        'debtToEquityRatio',
        'marketCap',
        'epsgrowth',
        'netIncomeGrowth',
        'operatingIncomeGrowth',
    ]

    df_factor = prepare_backtest_data(
        top_n=3000,
        factors=MY_FACTORS,
        universe_dict=universe_dict,
        parquet_filename=parquet_path,
    )
    df_factor_clean, report = clean_factor_panel(df_factor, verbose=True)

    filter_combo = {
        'returnOnEquity': ('upper', 0.3),
        'priceToEarningsRatio': ('lower', 0.3),
        'debtToEquityRatio': ('lower', 0.4),
        'freeCashFlow': ('upper', 0.8),
    }

    summary_combo, daily_ret_combo, timeline_combo = filtered_multifactor_test(
        df_data=df_factor_clean,
        universe_dict=universe_dict,
        top_n=3000,
        filter_conditions=filter_combo,
        name="ROE30_UP + PER30_DOWN + DE40_DOWN + FCF80_UP",
        cost_bps=20.0,
        start_date=None,
        end_date=None,
    )

    print("Finished.")