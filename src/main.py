"""Daily A-share AI agent concept report, powered by Eastmoney via AkShare."""
import os
from datetime import datetime
import requests
import akshare as ak

KEYWORDS = ("AI", "智能体", "AIAgent")

def pick_col(df, choices):
    return next((c for c in choices if c in df.columns), None)

def collect():
    boards = ak.stock_board_concept_name_em()
    name_col = pick_col(boards, ["板块名称", "名称"])
    if not name_col:
        raise RuntimeError(f"无法识别概念板块字段: {list(boards.columns)}")
    selected = boards[boards[name_col].astype(str).apply(lambda n: any(k.lower() in n.lower() for k in KEYWORDS))]
    if selected.empty:
        raise RuntimeError("未找到名称含 AI/智能体 的概念板块；请在 src/main.py 配置实际板块名")
    frames = []
    for board in selected[name_col].tolist():
        try:
            df = ak.stock_board_concept_cons_em(symbol=board)
            frames.append(df)
        except Exception as e:
            print(f"跳过板块 {board}: {e}")
    if not frames:
        raise RuntimeError("概念板块成分股获取失败")
    import pandas as pd
    all_df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["代码"])
    amount = pick_col(all_df, ["成交额", "成交额(元)"])
    change = pick_col(all_df, ["涨跌幅", "涨跌幅(%)"])
    code = pick_col(all_df, ["代码", "股票代码"])
    name = pick_col(all_df, ["名称", "股票简称"])
    if not all([amount, change, code, name]):
        raise RuntimeError(f"成分股行情字段不全: {list(all_df.columns)}")
    all_df[amount] = pd.to_numeric(all_df[amount], errors="coerce").fillna(0)
    all_df[change] = pd.to_numeric(all_df[change], errors="coerce").fillna(0)
    # Source lacks a consistently available net-flow field; use a transparent neutral component.
    all_df["_flow"] = 0.0
    def pct_rank(s):
        return s.rank(pct=True).fillna(0) * 100
    all_df["_score"] = .4*pct_rank(all_df[amount]) + .3*pct_rank(all_df[change]) + .2*pct_rank(all_df["_flow"]) + .1*50
    out=[]
    for _, row in all_df.nlargest(10, "_score").iterrows():
        ticker = str(row[code]).zfill(6)
        title, url = news(ticker, str(row[name]))
        summary = f"{row[name]}当日涨跌{float(row[change]):.2f}%，成交额{float(row[amount])/1e8:.2f}亿元；热度分{row['_score']:.1f}。"
        out.append((ticker, str(row[name]), summary[:49], title, url))
    return out

def news(code, name):
    try:
        df = ak.stock_news_em(symbol=code)
        if not df.empty:
            c = pick_col(df, ["新闻标题", "标题"]); u = pick_col(df, ["新闻链接", "链接"])
            if c and u:
                return str(df.iloc[0][c]), str(df.iloc[0][u])
    except Exception as e:
        print(f"新闻抓取失败 {code}: {e}")
    return f"{name}新闻搜索", f"https://so.eastmoney.com/news/s?keyword={name}"

def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    if not webhook:
        raise RuntimeError("请设置 FEISHU_WEBHOOK 环境变量")
    rows = collect()
    date = datetime.now().strftime("%Y-%m-%d")
    text = f"A股智能体概念股日报 {date}\n热度分=成交额40%+涨跌幅30%+资金净流入20%+新闻提及10%。行情源无一致可用的资金净流入/新闻量数据时，对该分项使用中性分，不伪造数值。\n\n"
    for i, (code, name, summary, title, url) in enumerate(rows, 1):
        text += f"{i}. {name} ({code})\n{summary}\n新闻：[ {title} ]({url})\n\n"
    resp = requests.post(webhook, json={"msg_type":"text", "content":{"text":text}}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code", 0) != 0:
        raise RuntimeError(f"飞书推送失败: {data}")
    print(text)

if __name__ == "__main__":
    main()

