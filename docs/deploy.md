# 飞书配置、部署与运行

## 运行要求

- 仓库 Actions Secret `FEISHU_WEBHOOK` 配置为飞书群自定义机器人 Webhook。切勿提交到代码或公开截图。
- 飞书自定义机器人关闭签名校验；本项目使用标准 Webhook。

## 部署与手动验证

1. 在飞书群添加自定义机器人，复制 Webhook。
2. GitHub 仓库 → Settings → Secrets and variables → Actions → New repository secret；名称填写 `FEISHU_WEBHOOK` 并保存。
3. 仓库 → Actions → A股智能体日报 → Run workflow，选择 `main` 并运行。
4. 成功后在飞书群确认日报。失败时在该次运行的 `report` job 查看错误日志。

## 定时安排

Cron 为 UTC `0 3 * * 1-5`，即北京时间周一至周五 11:00。GitHub Actions 定时可能略有延迟；工作日包含市场休市日，休市时行情数据为最近可用交易日。

## 评分与数据口径

通过 AkShare 获取东方财富概念成分、当日行情和今日个股主力净流入排名。成交额、涨跌幅、主力净流入使用全部识别成分股的横截面百分位。为避免东方财富对出口 IP 限流，程序先依这三项取基础分前 30 的候选，再串行获取候选个股新闻；新闻条数的 10%分项仅在这 30 只候选中计算百分位，最终由候选中选 Top 10。每股关键新闻链接取接口最新一条。这个候选限制是免费数据源稳定性的取舍，不等同于全体成分股新闻评分。

若东方财富触发短期限流，程序等待 6 分钟后重试一次；持续限流或接口/字段变化会令工作流失败，避免静默生成错误排名。可设置 `EASTMONEY_COOLDOWN_SECONDS` 调整等待时间。

## 流程图

见 [flowchart.mmd](flowchart.mmd)。
