"""Build a transparent market scorecard for European industrial companies."""

from __future__ import annotations

from html import escape
from pathlib import Path
import time

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
COMPANIES_PATH = ROOT / "data" / "companies.csv"
RESULTS_DIR = ROOT / "results"
TRADING_DAYS = 252


def load_prices(tickers: list[str]) -> pd.DataFrame:
    """Download two years of adjusted prices from Yahoo's chart endpoint."""
    series = {}
    headers = {"User-Agent": "Mozilla/5.0 (educational research project)"}
    for ticker in tickers:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        response = requests.get(
            url,
            params={"range": "2y", "interval": "1d", "events": "history"},
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()["chart"]["result"][0]
        dates = pd.to_datetime(result["timestamp"], unit="s").normalize()
        indicators = result["indicators"]
        values = indicators.get("adjclose", indicators["quote"])[0]
        closes = values["adjclose"] if "adjclose" in values else values["close"]
        series[ticker] = pd.Series(closes, index=dates, dtype="float64")
        time.sleep(0.15)

    prices = pd.DataFrame(series)
    if prices.empty:
        raise RuntimeError("No market data was returned.")
    return prices.sort_index().ffill().dropna(axis=1, how="all")


def trailing_return(series: pd.Series, sessions: int) -> float:
    clean = series.dropna()
    if len(clean) < sessions + 1:
        return float("nan")
    return clean.iloc[-1] / clean.iloc[-(sessions + 1)] - 1


def calculate_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    daily_returns = prices.pct_change(fill_method=None)
    metrics = pd.DataFrame(index=prices.columns)
    metrics["return_12m"] = [trailing_return(prices[c], 252) for c in prices]
    metrics["momentum_6m"] = [trailing_return(prices[c], 126) for c in prices]
    metrics["volatility_12m"] = daily_returns.tail(252).std() * TRADING_DAYS**0.5

    drawdowns = prices / prices.cummax() - 1
    metrics["max_drawdown_2y"] = drawdowns.min()

    metrics["return_score"] = metrics["return_12m"].rank(pct=True)
    metrics["momentum_score"] = metrics["momentum_6m"].rank(pct=True)
    metrics["volatility_score"] = (-metrics["volatility_12m"]).rank(pct=True)
    metrics["drawdown_score"] = metrics["max_drawdown_2y"].rank(pct=True)
    metrics["composite_score"] = 100 * (
        0.30 * metrics["return_score"]
        + 0.25 * metrics["momentum_score"]
        + 0.20 * metrics["volatility_score"]
        + 0.25 * metrics["drawdown_score"]
    )
    return metrics


def create_chart(scorecard: pd.DataFrame) -> None:
    """Write a dependency-free SVG that GitHub can render directly."""
    plot_data = scorecard.sort_values("composite_score", ascending=False).reset_index(drop=True)
    width, left, top, row_height = 920, 220, 90, 34
    height = top + len(plot_data) * row_height + 90
    chart_width = 640
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#101828}.label{font-size:13px}.value{font-size:12px;fill:#475467}.note{font-size:11px;fill:#667085}</style>',
        '<text x="24" y="34" font-size="22" font-weight="700">European Industrials Market Scorecard</text>',
        '<text x="24" y="58" class="note">Relative score based on momentum, volatility and drawdown resilience</text>',
    ]
    for index, row in plot_data.iterrows():
        y = top + index * row_height
        score = float(row["composite_score"])
        bar_width = chart_width * score / 100
        color = "#175cd3" if index < 3 else "#98a2b3"
        elements.extend(
            [
                f'<text x="24" y="{y + 16}" class="label">{escape(str(row["company"]))}</text>',
                f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="22" rx="3" fill="{color}"/>',
                f'<text x="{left + bar_width + 8:.1f}" y="{y + 16}" class="value">{score:.1f}</text>',
            ]
        )
    elements.extend(
        [
            f'<text x="24" y="{height - 38}" class="note">Weights: 12m return 30% | 6m momentum 25% | inverse volatility 20% | drawdown resilience 25%</text>',
            f'<text x="24" y="{height - 20}" class="note">Source: Yahoo Finance public chart endpoint. Educational analysis; not investment advice.</text>',
            "</svg>",
        ]
    )
    (RESULTS_DIR / "market_scorecard.svg").write_text("\n".join(elements), encoding="utf-8")


def main() -> None:
    companies = pd.read_csv(COMPANIES_PATH)
    prices = load_prices(companies["ticker"].tolist())
    metrics = calculate_metrics(prices)

    scorecard = companies.merge(metrics, left_on="ticker", right_index=True, how="inner")
    scorecard = scorecard.sort_values("composite_score", ascending=False)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    scorecard.to_csv(RESULTS_DIR / "scorecard.csv", index=False, float_format="%.4f")
    prices.to_csv(RESULTS_DIR / "adjusted_prices.csv", float_format="%.4f")
    create_chart(scorecard)

    display_columns = [
        "company",
        "return_12m",
        "momentum_6m",
        "volatility_12m",
        "max_drawdown_2y",
        "composite_score",
    ]
    print(scorecard[display_columns].to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(f"\nResults written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
