# 飞书配置及运行

1. 在飞书群添加自定义机器人，复制 Webhook URL（可开启签名校验；本项目当前仅支持无签名 Webhook）。
2. GitHub 仓库 Settings → Secrets and variables → Actions → New repository secret。名称填写 `FEISHU_WEBHOOK`，值粘贴机器人 Webhook。
3. 仓库 Actions 页面启用工作流。选择“ A股智能体日报 ”→ Run workflow 可手动试运行。
4. 成功后查看运行日志，并在飞书群确认消息。

工作流 cron 使用 UTC `0 3 * * 1-5`，对应北京时间周一至周五 11:00。GitHub Actions 定时任务可能延迟，且免费额度/私有仓库策略依 GitHub 账户方案而异。

本地验证：安装 Python 3.11，执行 `pip install -r requirements.txt`，设置环境变量 `FEISHU_WEBHOOK` 后运行 `python src/main.py`。

数据说明：AkShare 从 Eastmoney 获取概念板块和新闻。若板块命名/接口字段调整，运行会报错而非发出空榜单。当前净流入和新闻提及热度缺可靠统一数据字段时按中性值处理，因此需接入有授权的行情数据源后才能严格兑现原定的 20% 与新闻提及 10%评分。
