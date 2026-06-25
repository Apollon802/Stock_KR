#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_stock_master.py

Livermore Trend Analyzer v8용 kr_stock_master.json 자동 생성 스크립트.
- pykrx에서 KOSPI/KOSDAQ 종목명/코드 수집
- pykrx에서 국내 ETF 종목명/코드 수집 가능한 경우 추가
- Yahoo Finance 한국 심볼 규칙에 맞춰 KOSPI는 .KS, KOSDAQ은 .KQ 부여
- 결과 파일: kr_stock_master.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pykrx import stock

OUTPUT = Path("kr_stock_master.json")

# 자주 쓰는 별칭은 여기서 관리합니다.
ALIASES = {
    "삼성전자": ["삼전", "samsung"],
    "삼성전자우": ["삼전우"],
    "SK하이닉스": ["하이닉스", "sk hynix"],
    "NAVER": ["네이버"],
    "두산에너빌리티": ["두산중공업"],
    "리가켐바이오": ["레고켐바이오"],
    "JYP Ent.": ["JYP", "제이와이피", "JYP엔터"],
    "와이지엔터테인먼트": ["YG", "와이지"],
    "KODEX 200": ["코덱스200"],
    "TIGER 200": ["타이거200"],
    "TIGER 미국S&P500": ["타이거 미국S&P500", "TIGER S&P500"],
    "KODEX 미국S&P500": ["코덱스 미국S&P500"],
    "TIGER 미국나스닥100": ["타이거 나스닥100", "TIGER 나스닥100"],
    "KODEX 미국나스닥100": ["코덱스 나스닥100"],
}

US_ETFS = [
    {"name": "Invesco QQQ ETF", "symbol": "QQQ", "market": "US", "type": "ETF", "keywords": ["QQQ"]},
    {"name": "SPDR S&P 500 ETF", "symbol": "SPY", "market": "US", "type": "ETF", "keywords": ["SPY"]},
    {"name": "Vanguard S&P 500 ETF", "symbol": "VOO", "market": "US", "type": "ETF", "keywords": ["VOO"]},
    {"name": "Schwab US Dividend Equity ETF", "symbol": "SCHD", "market": "US", "type": "ETF", "keywords": ["SCHD"]},
    {"name": "iShares 20+ Year Treasury Bond ETF", "symbol": "TLT", "market": "US", "type": "ETF", "keywords": ["TLT"]},
    {"name": "VanEck Semiconductor ETF", "symbol": "SMH", "market": "US", "type": "ETF", "keywords": ["SMH"]},
]


def aliases_for(name: str) -> list[str]:
    return ALIASES.get(name, [])


def append_stock(items: list[dict], market: str) -> None:
    """KOSPI/KOSDAQ 종목 추가."""
    suffix = ".KS" if market == "KOSPI" else ".KQ"
    tickers = stock.get_market_ticker_list(market=market)
    for code in tickers:
        name = stock.get_market_ticker_name(code)
        if not name:
            continue
        items.append({
            "name": name,
            "symbol": f"{code}{suffix}",
            "market": market,
            "type": "STOCK",
            "keywords": aliases_for(name),
        })


def append_etf(items: list[dict]) -> None:
    """국내 ETF 추가. pykrx 버전에 따라 ETF 함수가 없을 수 있어 방어적으로 처리."""
    try:
        tickers = stock.get_etf_ticker_list()
    except Exception as exc:
        print(f"[WARN] ETF ticker list skipped: {exc}")
        return

    for code in tickers:
        try:
            name = stock.get_etf_ticker_name(code)
        except Exception:
            name = ""
        if not name:
            continue
        # 국내 ETF는 Yahoo Finance에서 대체로 .KS로 조회됩니다.
        items.append({
            "name": name,
            "symbol": f"{code}.KS",
            "market": "KOSPI",
            "type": "ETF",
            "keywords": aliases_for(name),
        })


def dedupe(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for item in items:
        key = item["symbol"]
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return sorted(out, key=lambda x: (x["market"], x["type"], x["name"]))


def main() -> None:
    items: list[dict] = []
    append_stock(items, "KOSPI")
    append_stock(items, "KOSDAQ")
    append_etf(items)
    items.extend(US_ETFS)
    items = dedupe(items)

    OUTPUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] wrote {OUTPUT} / count={len(items):,}")


if __name__ == "__main__":
    main()
