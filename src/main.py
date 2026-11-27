"""A股智能体概念股日报：Eastmoney data via AkShare, delivered to Feishu."""
import os
from datetime import datetime
import time
from zoneinfo import ZoneInfo

import akshare as ak
import pandas as pd
import requests

BEIJING = ZoneInfo("Asia/Shanghai")
CONCEPT_PATTERN = r"AI|AIAgent|智能体|大模型|人工智能"


def source_call(function, *args, **kwargs):
    """Retry Eastmoney's temporary Push2 IP ban once after its documented cooldown."""
    try:
        return function(*args, **kwargs)
    except Exception as exc:
        if "Push2RateLimitError" not in type(exc).__name__:
            raise
        wait_seconds = int(os.environ.get("EASTMONEY_COOLDOWN_SECONDS", "360"))
        print(f"Eastmoney temporary rate limit; wait {wait_seconds}s before one retry")
        time.sleep(wait_seconds)
        return function(*args, **kwargs)


def choose(df, *names):
    return next((name for name in names if name in df.columns), None)


def percentile(series):
    """Cross-sectional percentile; ties receive the average rank."""
    values = pd.to_numeric(series, errors="coerce")
    return values.rank(pct=True, method="average").fillna(0) * 100


def fetch_news(code, name, today):
    """Return today's news count and the most recent available title/link."""
    df = source_call(ak.stock_news_em, symbol=code)
    if df is None or df.empty:
        return code, 0, f"{name} 新闻搜索", f"https://so.eastmoney.com/news/s?keyword={name}"
    title_col = choose(df, "新闻标题", "标题", "title")
    url_col = choose(df, "新闻链接", "链接", "url")
    time_col = choose(df, "发布时间", "新闻时间", "public_time", "时间")
    if not title_col or not url_col or not time_col:
        raise RuntimeError(f"{code} 新闻字段变化: {list(df.columns)}")
    published = pd.to_datetime(df[time_col], errors="coerce")
    count = int((published.dt.date == today).sum())
    first = df.iloc[0]
    return code, count, str(first[title_col]), str(first[url_col])


def collect():
    boards = source_call(ak.stock_board_concept_name_em)
    board_col = choose(boards, "板块名称", "名称")
    if not board_col:
        raise RuntimeError(f"概念板块字段变化: {list(boards.columns)}")
    selected = boards[boards[board_col].astype(str).str.contains(CONCEPT_PATTERN, case=False, regex=True)]
    if selected.empty:
        raise RuntimeError("没有找到 AI/智能体相关概念板块，请检查 Eastmoney 当前板块名称")

    frames = []
    for board in selected[board_col].tolist():
        frame = source_call(ak.stock_board_concept_cons_em, symbol=board)
        if frame is not None and not frame.empty:
            frames.append(frame)
    if not frames:
        raise RuntimeError("概念板块成分股为空")
    stocks = pd.concat(frames, ignore_index=True)
    code_col = choose(stocks, "代码", "股票代码")
    name_col = choose(stocks, "名称", "股票简称")
    amount_col = choose(stocks, "成交额", "成交额(元)")
    change_col = choose(stocks, "涨跌幅", "涨跌幅(%)")
    if not all((code_col, name_col, amount_col, change_col)):
        raise RuntimeError(f"成分股行情字段变化: {list(stocks.columns)}")
    stocks[code_col] = stocks[code_col].astype(str).str.zfill(6)
    stocks = stocks.drop_duplicates(subset=[code_col]).copy()
    stocks[amount_col] = pd.to_numeric(stocks[amount_col], errors="coerce")
    stocks[change_col] = pd.to_numeric(stocks[change_col], errors="coerce")

    # One Eastmoney ranking request provides today's main net inflow for the market.
    flow = source_call(ak.stock_individual_fund_flow_rank, indicator="今日")
    flow_code = choose(flow, "代码", "股票代码")
    flow_value = choose(flow, "今日主力净流入-净额", "主力净流入-净额", "今日主力净流入", "主力净流入")
    if not flow_code or not flow_value:
        raise RuntimeError(f"资金流字段变化: {list(flow.columns)}")
    flow = flow[[flow_code, flow_value]].copy()
    flow[flow_code] = flow[flow_code].astype(str).str.zfill(6)
    flow[flow_value] = pd.to_numeric(flow[flow_value], errors="coerce")
    stocks = stocks.merge(flow, left_on=code_col, right_on=flow_code, how="left")
    if stocks[flow_value].isna().all():
        raise RuntimeError("概念成分股未匹配到当日主力净流入数据")

    # Bound per-stock news requests: first shortlist by the 90% of metrics available
    # in bulk, then fetch news serially for the strongest 30 candidates.
    stocks["_base_score"] = (
        0.40 * percentile(stocks[amount_col])
        + 0.30 * percentile(stocks[change_col])
        + 0.20 * percentile(stocks[flow_value])
    )
    candidates = stocks.nlargest(min(30, len(stocks)), "_base_score").copy()
    today = datetime.now(BEIJING).date()
    news_data = {}
    for _, row in candidates.iterrows():
        code, count, title, url = fetch_news(row[code_col], str(row[name_col]), today)
        news_data[code] = (count, title, url)
        time.sleep(0.6)
    candidates["_news_count"] = candidates[code_col].map(lambda code: news_data[code][0])
    candidates["_news_title"] = candidates[code_col].map(lambda code: news_data[code][1])
    candidates["_news_url"] = candidates[code_col].map(lambda code: news_data[code][2])

    candidates["_score"] = (
        candidates["_base_score"]
        + 0.10 * percentile(candidates["_news_count"])
    )
    top = candidates.nlargest(10, "_score")
    result = []
    for _, row in top.iterrows():
        amount_yi = float(row[amount_col]) / 1e8
        flow_yi = float(row[flow_value]) / 1e8
        summary = (
            f"{row[name_col]}涨跌{float(row[change_col]):.2f}%，成交额{amount_yi:.2f}亿元，"
            f"主力净流入{flow_yi:.2f}亿元，今日新闻{int(row['_news_count'])}条。"
        )
        result.append({
            "code": row[code_col], "name": row[name_col], "summary": summary,
            "score": float(row["_score"]), "news_title": row["_news_title"], "news_url": row["_news_url"],
        })
    return result


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    if not webhook:
        raise RuntimeError("缺少 GitHub Actions Secret: FEISHU_WEBHOOK")
    report_date = datetime.now(BEIJING).strftime("%Y-%m-%d")
    rows = collect()
    lines = [
        f"A股 AI/智能体概念股日报 {report_date}",
        "综合热度分 = 成交额40% + 涨跌幅30% + 主力净流入20% + 当日个股新闻条数10%；新闻项在基础分前30候选股中排名。",
        "数据源：东方财富，经 AkShare 获取；新闻数为东方财富个股新闻接口当日记录数。仅供信息参考，不构成投资建议。", "",
    ]
    for i, row in enumerate(rows, 1):
        lines.extend([
            f"{i}. {row['name']}（{row['code']}）｜热度 {row['score']:.1f}",
            row["summary"],
            f"关键新闻：{row['news_title']} {row['news_url']}", "",
        ])
    message = "\n".join(lines)
    response = requests.post(
        webhook, json={"msg_type": "text", "content": {"text": message}}, timeout=30
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code", 0) != 0:
        raise RuntimeError(f"飞书机器人返回错误: {payload}")
    print(message)


if __name__ == "__main__":
    main()
