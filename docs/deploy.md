# 飞书配置、部署与运行

## 运行要求

- GitHub 仓库中已提交 `.github/workflows/daily.yml`。
- 仓库 Actions Secret 名称为 `FEISHU_WEBHOOK`，值为飞书群自定义机器人的 Webhook。切勿提交到代码或公开截图。
- 飞书自定义机器人关闭签名校验；本项目使用标准 Webhook。

## 部署与手动验证

1. 在飞书群添加自定义机器人，复制 Webhook。
2. GitHub 仓库 → Settings → Secrets and variables → Actions → New repository secret；名称填写 `FEISHU_WEBHOOK`，保存。
3. 仓库 → Actions → A股智能体日报 → Run workflow，选择 `main` 并运行。
4. 成功后在飞书群确认日报。失败时在该次运行的 `report` job 查看错误日志。

## 定时安排

Cron 为 UTC `0 3 * * 1-5`，即北京时间周一至周五 11:00。GitHub Actions 定时触发可能有延迟；工作日包括市场休市日，休市时行情数据可能是最近交易日数据。

## 评分与数据口径

使用东方财富经 AkShare 提供的概念板块成分、当日行情、个股主力资金流排名和个股新闻。先从板块名称中匹配 AI、AIAgent、智能体、大模型、人工智能相关板块，合并去重后，对成交额、涨跌幅、主力净流入额、当日个股新闻条数分别计算横截面百分位，再按 40/30/20/10 加权排序。摘要控制在 50 字以内，新闻链接取该股新闻接口最新一条记录。

源接口或字段异常时工作流失败，不退回虚构/中性数据。免费公开源可能限流或变更；需检查 Actions 日志并更新 AkShare/字段适配。

## 流程图

见 [flowchart.mmd](flowchart.mmd)。
