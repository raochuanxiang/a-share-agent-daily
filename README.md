# A股智能体概念股日报

GitHub Actions 工作日北京时间 11:00 获取东方财富 AI/智能体概念板块，按成交额40%、涨跌幅30%、主力净流入20%、当日个股新闻条数10%的横截面百分位综合分选 Top 10，推送飞书。

- 流程图：[docs/flowchart.mmd](docs/flowchart.mmd)
- 部署说明：[docs/deploy.md](docs/deploy.md)
- 飞书机器人 Webhook 通过 Actions Secret `FEISHU_WEBHOOK` 提供。

数据由 AkShare 转接东方财富公开接口；接口变更或缺字段会让运行失败以避免静默生成错误排名。新闻热度以各股新闻接口当天返回记录数近似。仅供信息参考，不构成投资建议。
